import Foundation
import StoreKit

/// StoreKit 2 — Premium (reklamsız, sınırsız ürün) satın alma ve entitlement takibi.
@MainActor
final class PremiumStoreService: ObservableObject {
    static let shared = PremiumStoreService()

    static let productID = "com.tagtrack.app.premium"
    static let freeProductLimit = 5

    @Published private(set) var isPremium = false
    @Published private(set) var premiumProduct: StoreKit.Product?
    @Published var purchaseError: String?
    @Published var isPurchasing = false

    private var updatesTask: Task<Void, Never>?

    private init() {
        updatesTask = listenForTransactions()
        Task { await refreshEntitlements() }
    }

    deinit {
        updatesTask?.cancel()
    }

    var canAddMoreProducts: Bool {
        isPremium || LocalStorageService.shared.loadProducts().count < Self.freeProductLimit
    }

    var remainingFreeSlots: Int {
        max(0, Self.freeProductLimit - LocalStorageService.shared.loadProducts().count)
    }

    func loadProducts() async {
        do {
            let products = try await StoreKit.Product.products(for: [Self.productID])
            premiumProduct = products.first
        } catch {
            purchaseError = "Premium ürün bilgisi yüklenemedi."
        }
    }

    func purchase() async {
        guard let product = premiumProduct else {
            purchaseError = "Premium ürün App Store'da henüz yapılandırılmamış olabilir."
            return
        }
        isPurchasing = true
        purchaseError = nil
        defer { isPurchasing = false }

        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                let transaction = try checkVerified(verification)
                await transaction.finish()
                await refreshEntitlements()
            case .userCancelled:
                break
            case .pending:
                purchaseError = "Satın alma onay bekliyor."
            @unknown default:
                break
            }
        } catch {
            purchaseError = error.localizedDescription
        }
    }

    func restorePurchases() async {
        isPurchasing = true
        purchaseError = nil
        defer { isPurchasing = false }
        try? await AppStore.sync()
        await refreshEntitlements()
        if !isPremium {
            purchaseError = "Geri yüklenecek satın alma bulunamadı."
        }
    }

    func refreshEntitlements() async {
        var hasPremium = false
        for await result in StoreKit.Transaction.currentEntitlements {
            guard let transaction = try? checkVerified(result) else { continue }
            if transaction.productID == Self.productID, transaction.revocationDate == nil {
                hasPremium = true
            }
        }
        isPremium = hasPremium
        UserDefaults.standard.set(hasPremium, forKey: "isPremium")
    }

    private func listenForTransactions() -> Task<Void, Never> {
        Task {
            for await result in StoreKit.Transaction.updates {
                if let transaction = try? checkVerified(result) {
                    await transaction.finish()
                    await refreshEntitlements()
                }
            }
        }
    }

    private func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified:
            throw StoreError.failedVerification
        case .verified(let safe):
            return safe
        }
    }

    private enum StoreError: Error {
        case failedVerification
    }
}
