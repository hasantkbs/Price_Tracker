import Foundation

class PriceCheckService {
    static let shared = PriceCheckService()
    private init() {}

    /// Tüm ürünlerin fiyatını arka planda kontrol eder, alarm koşullarını değerlendirir.
    func checkAllPrices() async {
        let products = LocalStorageService.shared.loadProducts()
        await withTaskGroup(of: Void.self) { group in
            for product in products {
                group.addTask { await self.checkPrice(for: product) }
            }
        }
    }

    /// Tek bir ürünün fiyatını kontrol edip kaydeder ve gerekirse bildirim gönderir.
    @discardableResult
    func checkPrice(for product: Product) async -> Product {
        var updated = product
        do {
            let result = try await WebScraperService.shared.fetchPrice(from: product.url)
            updated.currentPrice = result.price
            updated.lastCheckedAt = Date()
            updated.lastPriceSource = result.source

            if updated.initialPrice == nil {
                updated.initialPrice = result.price
            }

            let entry = PriceHistoryEntry(price: result.price, source: result.source)
            updated.priceHistory.append(entry)

            // Bildirim kontrolü
            if updated.alertTriggered {
                NotificationService.shared.scheduleAlert(for: updated, currentPrice: result.price)
            }

            LocalStorageService.shared.updateProduct(updated)
        } catch {
            // Sessizce geç - bir sonraki kontrolde tekrar denenecek
        }
        return updated
    }
}
