import Foundation

enum ScraperError: LocalizedError {
    case invalidURL
    case networkError(Error)
    case priceNotFound
    case httpError(Int)

    var errorDescription: String? {
        switch self {
        case .invalidURL:           return "Geçersiz URL"
        case .networkError(let e): return "Ağ hatası: \(e.localizedDescription)"
        case .priceNotFound:        return "Fiyat sayfada bulunamadı"
        case .httpError(let code): return "HTTP hatası (\(code))"
        }
    }
}

struct ScrapeResult {
    let price: Double
    let source: String
}

class WebScraperService {
    static let shared = WebScraperService()
    private init() {}

    // MARK: - Public API

    func fetchPrice(from urlString: String) async throws -> ScrapeResult {
        guard let url = URL(string: urlString) else { throw ScraperError.invalidURL }

        var request = URLRequest(url: url, timeoutInterval: 25)
        request.setValue(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            forHTTPHeaderField: "User-Agent"
        )
        request.setValue("text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", forHTTPHeaderField: "Accept")
        request.setValue("tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7", forHTTPHeaderField: "Accept-Language")
        request.setValue("gzip, deflate, br", forHTTPHeaderField: "Accept-Encoding")

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw ScraperError.networkError(error)
        }

        if let http = response as? HTTPURLResponse, http.statusCode >= 400 {
            throw ScraperError.httpError(http.statusCode)
        }

        guard let html = String(data: data, encoding: .utf8)
                      ?? String(data: data, encoding: .isoLatin1) else {
            throw ScraperError.priceNotFound
        }

        if let result = extractFromJSONLD(html)    { return result }
        if let result = extractFromMetaTags(html)  { return result }
        if let result = extractFromMicrodata(html) { return result }
        if let result = extractFromHTML(html)      { return result }

        throw ScraperError.priceNotFound
    }

    // MARK: - Extraction Methods

    private func extractFromJSONLD(_ html: String) -> ScrapeResult? {
        let blockPattern = #"<script[^>]*type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>"#
        guard let regex = try? NSRegularExpression(pattern: blockPattern, options: .caseInsensitive) else { return nil }

        let nsHtml = html as NSString
        let matches = regex.matches(in: html, range: NSRange(location: 0, length: nsHtml.length))

        for match in matches {
            guard match.numberOfRanges > 1 else { continue }
            let jsonStr = nsHtml.substring(with: match.range(at: 1))
            guard let jsonData = jsonStr.data(using: .utf8),
                  let json = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any]
            else { continue }

            if let price = extractPriceFromJSONLDObject(json) {
                return ScrapeResult(price: price, source: "json_ld")
            }
        }
        return nil
    }

    private func extractPriceFromJSONLDObject(_ json: [String: Any]) -> Double? {
        if let price = json["price"], let p = toDouble(price) { return p }

        if let offers = json["offers"] as? [String: Any] {
            if let price = offers["price"], let p = toDouble(price) { return p }
            if let lowPrice = offers["lowPrice"], let p = toDouble(lowPrice) { return p }
        }

        if let offersArr = json["offers"] as? [[String: Any]] {
            for offer in offersArr {
                if let price = offer["price"], let p = toDouble(price) { return p }
            }
        }

        if let graph = json["@graph"] as? [[String: Any]] {
            for node in graph {
                if let price = extractPriceFromJSONLDObject(node) { return price }
            }
        }
        return nil
    }

    private func extractFromMetaTags(_ html: String) -> ScrapeResult? {
        let patterns = [
            #"<meta[^>]*property=["\']product:price:amount["\'][^>]*content=["\']([^"\']+)["\']"#,
            #"<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']product:price:amount["\']"#,
            #"<meta[^>]*itemprop=["\']price["\'][^>]*content=["\']([^"\']+)["\']"#,
            #"<meta[^>]*content=["\']([^"\']+)["\'][^>]*itemprop=["\']price["\']"#,
            #"<meta[^>]*name=["\']twitter:data1["\'][^>]*content=["\']([^"\']+)["\']"#,
        ]
        let nsHtml = html as NSString
        for pattern in patterns {
            guard let regex = try? NSRegularExpression(pattern: pattern, options: .caseInsensitive) else { continue }
            if let match = regex.firstMatch(in: html, range: NSRange(location: 0, length: nsHtml.length)),
               match.numberOfRanges > 1 {
                let text = nsHtml.substring(with: match.range(at: 1))
                if let price = parsePrice(text) {
                    return ScrapeResult(price: price, source: "meta_tags")
                }
            }
        }
        return nil
    }

    private func extractFromMicrodata(_ html: String) -> ScrapeResult? {
        let patterns = [
            #"itemprop=["\']price["\'][^>]*content=["\']([^"\']+)["\']"#,
            #"content=["\']([^"\']+)["\'][^>]*itemprop=["\']price["\']"#,
        ]
        let nsHtml = html as NSString
        for pattern in patterns {
            guard let regex = try? NSRegularExpression(pattern: pattern, options: .caseInsensitive) else { continue }
            if let match = regex.firstMatch(in: html, range: NSRange(location: 0, length: nsHtml.length)),
               match.numberOfRanges > 1 {
                let text = nsHtml.substring(with: match.range(at: 1))
                if let price = parsePrice(text) {
                    return ScrapeResult(price: price, source: "microdata")
                }
            }
        }
        return nil
    }

    private func extractFromHTML(_ html: String) -> ScrapeResult? {
        // Common price-adjacent patterns for Turkish and international sites
        let patterns = [
            // Turkish lira patterns with context
            #"(?:fiyat|price|prc|pris|amount|cost)[^<]{0,150}?(\d{1,3}(?:\.\d{3})*,\d{2})\s*(?:TL|₺)"#,
            #"(\d{1,3}(?:\.\d{3})*,\d{2})\s*(?:TL|₺)"#,
            // USD/EUR patterns
            #"(?:\$|€)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"#,
            #"(\d{1,3}(?:,\d{3})*\.\d{2})\s*(?:\$|€|USD|EUR)"#,
            // Generic decimal
            #"(?:fiyat|price)[^<]{0,100}?(\d+[.,]\d{2})"#,
        ]
        let nsHtml = html as NSString
        for pattern in patterns {
            guard let regex = try? NSRegularExpression(
                pattern: pattern,
                options: [.caseInsensitive, .dotMatchesLineSeparators]
            ) else { continue }

            if let match = regex.firstMatch(in: html, range: NSRange(location: 0, length: nsHtml.length)),
               match.numberOfRanges > 1 {
                let text = nsHtml.substring(with: match.range(at: 1))
                if let price = parsePrice(text) {
                    return ScrapeResult(price: price, source: "html_pattern")
                }
            }
        }
        return nil
    }

    // MARK: - Price Parsing (port from price_utils.py)

    func parsePrice(_ raw: String) -> Double? {
        var text = raw
        for symbol in ["₺", "TL", "TRY", "$", "€", "EUR", "USD", "\u{00A0}", " "] {
            text = text.replacingOccurrences(of: symbol, with: "")
        }
        text = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return nil }

        // Turkish: 1.299,00  or  1299,00
        let turkishPattern = #"^\d{1,3}(?:\.\d{3})*,\d{2}$"#
        if matches(text, pattern: turkishPattern) {
            let normalized = text.replacingOccurrences(of: ".", with: "").replacingOccurrences(of: ",", with: ".")
            return Double(normalized)
        }

        // English: 1,299.00  or  1299.00
        let englishPattern = #"^\d{1,3}(?:,\d{3})*\.\d{2}$"#
        if matches(text, pattern: englishPattern) {
            return Double(text.replacingOccurrences(of: ",", with: ""))
        }

        // Comma-only decimal (e.g. 999,5)
        if text.contains(",") && !text.contains(".") {
            return Double(text.replacingOccurrences(of: ",", with: "."))
        }

        // Plain number
        return Double(text)
    }

    private func matches(_ text: String, pattern: String) -> Bool {
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return false }
        let range = NSRange(text.startIndex..., in: text)
        return regex.firstMatch(in: text, range: range) != nil
    }

    private func toDouble(_ value: Any) -> Double? {
        if let d = value as? Double { return d }
        if let i = value as? Int { return Double(i) }
        if let s = value as? String { return parsePrice(s) }
        return nil
    }
}
