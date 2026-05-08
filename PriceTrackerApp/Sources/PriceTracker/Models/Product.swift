import Foundation

struct Product: Codable, Identifiable {
    var id: UUID
    var url: String
    var name: String?
    var targetPrice: Double
    var currentPrice: Double?
    var initialPrice: Double?
    var createdAt: Date
    var lastCheckedAt: Date?
    var alertPrice: Double?
    var alertEnabled: Bool
    var priceHistory: [PriceHistoryEntry]
    var lastPriceSource: String?

    init(
        url: String,
        name: String?,
        targetPrice: Double,
        currentPrice: Double?,
        alertPrice: Double?
    ) {
        self.id = UUID()
        self.url = url
        self.name = name
        self.targetPrice = targetPrice
        self.currentPrice = currentPrice
        self.initialPrice = currentPrice
        self.createdAt = Date()
        self.lastCheckedAt = nil
        self.alertPrice = alertPrice
        self.alertEnabled = alertPrice != nil
        self.priceHistory = []
        self.lastPriceSource = nil
    }

    var displayName: String {
        if let n = name, !n.isEmpty { return n }
        if let host = URL(string: url)?.host { return host }
        return url
    }

    var isAlertEnabled: Bool { alertEnabled }

    var priceChangePercent: Double? {
        guard let current = currentPrice,
              let initial = initialPrice,
              initial > 0 else { return nil }
        return ((current - initial) / initial) * 100.0
    }

    var isTargetReached: Bool {
        guard let current = currentPrice else { return false }
        return current <= targetPrice
    }

    var alertTriggered: Bool {
        guard alertEnabled, let current = currentPrice, let alert = alertPrice else { return false }
        return current <= alert
    }
}

struct PriceHistoryEntry: Codable, Identifiable {
    var id: UUID
    let price: Double
    let source: String?
    let recordedAt: Date

    init(price: Double, source: String?) {
        self.id = UUID()
        self.price = price
        self.source = source
        self.recordedAt = Date()
    }

    var formattedDate: String {
        let f = DateFormatter()
        f.dateFormat = "dd.MM.yyyy HH:mm"
        return f.string(from: recordedAt)
    }
}
