import Foundation
import SwiftUI

@MainActor
class ProductsViewModel: ObservableObject {
    @Published var products: [Product] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    // MARK: - Load

    func loadProducts() {
        products = LocalStorageService.shared.loadProducts()
    }

    // MARK: - Add

    func addProduct(url: String, name: String?, targetPrice: Double, currentPrice: Double, alertPrice: Double?) {
        var product = Product(
            url: url,
            name: name,
            targetPrice: targetPrice,
            currentPrice: currentPrice,
            alertPrice: alertPrice
        )
        let entry = PriceHistoryEntry(price: currentPrice, source: "manual")
        product.priceHistory.append(entry)
        product.lastCheckedAt = Date()
        LocalStorageService.shared.addProduct(product)
        loadProducts()
    }

    // MARK: - Delete

    func deleteProduct(id: UUID) {
        LocalStorageService.shared.deleteProduct(id: id)
        products.removeAll { $0.id == id }
    }

    // MARK: - Update

    func updateProduct(_ product: Product) {
        LocalStorageService.shared.updateProduct(product)
        if let idx = products.firstIndex(where: { $0.id == product.id }) {
            products[idx] = product
        }
        successMessage = "Ürün güncellendi"
    }

    // MARK: - Price Check

    func checkPrice(for product: Product) async {
        guard let idx = products.firstIndex(where: { $0.id == product.id }) else { return }
        isLoading = true
        defer { isLoading = false }
        let updated = await PriceCheckService.shared.checkPrice(for: product)
        products[idx] = updated
    }

    func checkAllPrices() async {
        isLoading = true
        defer { isLoading = false }
        await PriceCheckService.shared.checkAllPrices()
        loadProducts()
    }

    // MARK: - Helpers

    func clearError()   { errorMessage = nil }
    func clearSuccess() { successMessage = nil }
}
