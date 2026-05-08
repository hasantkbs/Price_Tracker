import Foundation

class LocalStorageService {
    static let shared = LocalStorageService()
    private init() {}

    private let fileName = "products.json"

    private var fileURL: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent(fileName)
    }

    private let encoder: JSONEncoder = {
        let e = JSONEncoder()
        e.dateEncodingStrategy = .iso8601
        return e
    }()

    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.dateDecodingStrategy = .iso8601
        return d
    }()

    func loadProducts() -> [Product] {
        guard let data = try? Data(contentsOf: fileURL) else { return [] }
        return (try? decoder.decode([Product].self, from: data)) ?? []
    }

    func saveProducts(_ products: [Product]) {
        guard let data = try? encoder.encode(products) else { return }
        try? data.write(to: fileURL, options: .atomic)
    }

    func addProduct(_ product: Product) {
        var products = loadProducts()
        products.append(product)
        saveProducts(products)
    }

    func updateProduct(_ product: Product) {
        var products = loadProducts()
        if let idx = products.firstIndex(where: { $0.id == product.id }) {
            products[idx] = product
        }
        saveProducts(products)
    }

    func deleteProduct(id: UUID) {
        var products = loadProducts()
        products.removeAll { $0.id == id }
        saveProducts(products)
    }
}
