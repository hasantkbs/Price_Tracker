import SwiftUI

struct AddProductView: View {
    @Environment(\.dismiss) private var dismiss
    let onAdded: () -> Void

    @State private var urlText = ""
    @State private var name = ""
    @State private var targetPrice = ""
    @State private var enableAlert = false
    @State private var alertPrice = ""

    @State private var isFetchingPrice = false
    @State private var fetchedPrice: Double?
    @State private var fetchSource: String?
    @State private var fetchError: String?
    @State private var isSaving = false

    var body: some View {
        NavigationView {
            Form {
                // URL Section
                Section(
                    header: Text("Ürün Bağlantısı"),
                    footer: Text("URL girdikten sonra fiyatı otomatik çekeceğiz.")
                ) {
                    TextField("https://...", text: $urlText)
                        .textContentType(.URL)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)
                        .submitLabel(.done)
                        .onSubmit { fetchPriceFromURL() }

                    TextField("Ürün adı (opsiyonel)", text: $name)
                }

                // Price Fetch Section
                Section(header: Text("Mevcut Fiyat")) {
                    if isFetchingPrice {
                        HStack {
                            ProgressView()
                                .scaleEffect(0.85)
                            Text("Fiyat çekiliyor...")
                                .foregroundColor(.secondary)
                                .font(.subheadline)
                        }
                    } else if let price = fetchedPrice {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(String(format: "%.2f ₺", price))
                                    .font(.headline)
                                    .foregroundColor(.green)
                                if let source = fetchSource {
                                    Text("Kaynak: \(sourceLabel(source))")
                                        .font(.caption2)
                                        .foregroundColor(.secondary)
                                }
                            }
                            Spacer()
                            Button("Yenile") { fetchPriceFromURL() }
                                .font(.caption)
                                .foregroundColor(.blue)
                        }
                    } else {
                        Button(action: fetchPriceFromURL) {
                            HStack {
                                Image(systemName: "arrow.down.circle")
                                Text("Fiyatı Otomatik Çek")
                            }
                        }
                        .disabled(urlText.trimmingCharacters(in: .whitespaces).isEmpty)

                        if let err = fetchError {
                            Text(err)
                                .font(.caption)
                                .foregroundColor(.red)
                        }
                    }
                }

                // Target Price
                Section(footer: Text("Bu fiyata ulaştığında bildirim alabilirsiniz.")) {
                    HStack {
                        Text("Hedef Fiyat")
                        Spacer()
                        TextField("0.00", text: $targetPrice)
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.trailing)
                            .frame(width: 110)
                    }
                }

                // Alert
                Section(header: Text("Fiyat Alarmı")) {
                    Toggle("Alarm kur", isOn: $enableAlert.animation())
                    if enableAlert {
                        HStack {
                            Text("Alarm Fiyatı")
                            Spacer()
                            TextField("0.00", text: $alertPrice)
                                .keyboardType(.decimalPad)
                                .multilineTextAlignment(.trailing)
                                .frame(width: 110)
                        }
                    }
                }
            }
            .navigationTitle("Ürün Ekle")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("İptal") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    if isSaving {
                        ProgressView()
                    } else {
                        Button("Ekle") { save() }
                            .fontWeight(.semibold)
                            .disabled(!canSave)
                    }
                }
            }
        }
    }

    // MARK: - Logic

    private var canSave: Bool {
        !urlText.trimmingCharacters(in: .whitespaces).isEmpty
            && fetchedPrice != nil
            && !targetPrice.trimmingCharacters(in: .whitespaces).isEmpty
    }

    private func fetchPriceFromURL() {
        let trimmed = urlText.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        isFetchingPrice = true
        fetchError = nil
        fetchedPrice = nil

        Task {
            do {
                let result = try await WebScraperService.shared.fetchPrice(from: trimmed)
                await MainActor.run {
                    fetchedPrice = result.price
                    fetchSource = result.source
                    isFetchingPrice = false
                }
            } catch {
                await MainActor.run {
                    fetchError = error.localizedDescription
                    isFetchingPrice = false
                }
            }
        }
    }

    private func save() {
        guard PremiumStoreService.shared.canAddMoreProducts else {
            fetchError = "Ücretsiz planda en fazla \(PremiumStoreService.freeProductLimit) ürün ekleyebilirsiniz."
            return
        }
        guard let currentPrice = fetchedPrice else { return }
        let targetVal = Double(targetPrice.replacingOccurrences(of: ",", with: ".")) ?? 0
        let alertVal = enableAlert
            ? Double(alertPrice.replacingOccurrences(of: ",", with: "."))
            : nil

        isSaving = true
        var product = Product(
            url: urlText.trimmingCharacters(in: .whitespaces),
            name: name.isEmpty ? nil : name,
            targetPrice: targetVal,
            currentPrice: currentPrice,
            alertPrice: alertVal
        )
        let entry = PriceHistoryEntry(price: currentPrice, source: fetchSource ?? "auto")
        product.priceHistory.append(entry)
        product.lastCheckedAt = Date()
        product.lastPriceSource = fetchSource

        LocalStorageService.shared.addProduct(product)
        onAdded()
        dismiss()
    }

    private func sourceLabel(_ source: String) -> String {
        switch source {
        case "json_ld":      return "JSON-LD"
        case "meta_tags":    return "Meta Tag"
        case "microdata":    return "Microdata"
        case "html_pattern": return "HTML"
        default:             return source
        }
    }
}
