import SwiftUI

struct EditProductView: View {
    @ObservedObject var viewModel: ProductsViewModel
    @Environment(\.dismiss) private var dismiss

    @State private var product: Product

    @State private var name: String
    @State private var targetPrice: String
    @State private var alertEnabled: Bool
    @State private var alertPrice: String
    @State private var isSaving = false
    @State private var isCheckingPrice = false

    init(product: Product, viewModel: ProductsViewModel) {
        self._product = State(initialValue: product)
        self.viewModel = viewModel
        _name = State(initialValue: product.name ?? "")
        _targetPrice = State(initialValue: String(format: "%.2f", product.targetPrice))
        _alertEnabled = State(initialValue: product.isAlertEnabled)
        _alertPrice = State(initialValue: product.alertPrice.map { String(format: "%.2f", $0) } ?? "")
    }

    var body: some View {
        Form {
            productSection
            pricesSection
            alarmSection
            actionsSection
            historySection
        }
        .navigationTitle(product.displayName)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                if isSaving {
                    ProgressView()
                } else {
                    Button("Kaydet") { save() }
                        .fontWeight(.semibold)
                }
            }
        }
        .alert("Başarılı", isPresented: Binding(
            get: { viewModel.successMessage != nil },
            set: { if !$0 { viewModel.clearSuccess() } }
        )) {
            Button("Tamam") { viewModel.clearSuccess() }
        } message: {
            Text(viewModel.successMessage ?? "")
        }
        .alert("Hata", isPresented: Binding(
            get: { viewModel.errorMessage != nil },
            set: { if !$0 { viewModel.clearError() } }
        )) {
            Button("Tamam") { viewModel.clearError() }
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
    }

    // MARK: - Sections

    private var productSection: some View {
        Section(header: Text("Ürün")) {
            TextField("Ürün adı", text: $name)
            if let productURL = URL(string: product.url) {
                Link(destination: productURL) {
                    Label("Ürün sayfasını aç", systemImage: "safari")
                        .font(.footnote)
                }
            }
        }
    }

    private var pricesSection: some View {
        Section(header: Text("Fiyatlar")) {
            infoRow(label: "Mevcut Fiyat",
                    value: product.currentPrice.map { String(format: "%.2f ₺", $0) } ?? "—",
                    valueColor: currentPriceColor)
            infoRow(label: "İlk Fiyat",
                    value: product.initialPrice.map { String(format: "%.2f ₺", $0) } ?? "—",
                    valueColor: .secondary)
            if let source = product.lastPriceSource {
                infoRow(label: "Veri Kaynağı", value: source.uppercased(), valueColor: .secondary)
            }
            HStack {
                Text("Hedef Fiyat")
                Spacer()
                TextField("0.00", text: $targetPrice)
                    .keyboardType(.decimalPad)
                    .multilineTextAlignment(.trailing)
                    .frame(width: 110)
            }
        }
    }

    private var alarmSection: some View {
        Section(header: Text("Alarm")) {
            Toggle("Fiyat alarmı", isOn: $alertEnabled.animation())
            if alertEnabled {
                HStack {
                    Text("Alarm fiyatı")
                    Spacer()
                    TextField("0.00", text: $alertPrice)
                        .keyboardType(.decimalPad)
                        .multilineTextAlignment(.trailing)
                        .frame(width: 110)
                }
            }
        }
    }

    private var actionsSection: some View {
        Section {
            Button(action: checkPriceNow) {
                HStack {
                    if isCheckingPrice {
                        ProgressView().scaleEffect(0.8)
                    } else {
                        Image(systemName: "arrow.clockwise.circle")
                    }
                    Text(isCheckingPrice ? "Kontrol ediliyor..." : "Fiyatı şimdi kontrol et")
                }
            }
            .disabled(isCheckingPrice)
        }
    }

    private var historySection: some View {
        Section(header: Text("Fiyat Geçmişi")) {
            if product.priceHistory.isEmpty {
                Text("Henüz geçmiş kayıt yok")
                    .font(.caption)
                    .foregroundColor(.secondary)
            } else {
                ForEach(product.priceHistory.reversed().prefix(15)) { entry in
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(String(format: "%.2f ₺", entry.price))
                                .font(.subheadline)
                                .fontWeight(.medium)
                            if let source = entry.source {
                                Text(source.uppercased())
                                    .font(.caption2)
                                    .foregroundColor(.secondary)
                            }
                        }
                        Spacer()
                        Text(entry.formattedDate)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
    }

    // MARK: - Helpers

    @ViewBuilder
    private func infoRow(label: String, value: String, valueColor: Color) -> some View {
        HStack {
            Text(label)
            Spacer()
            Text(value).foregroundColor(valueColor)
        }
    }

    private var currentPriceColor: Color {
        guard let current = product.currentPrice else { return .primary }
        return current <= product.targetPrice ? .green : .primary
    }

    private func checkPriceNow() {
        isCheckingPrice = true
        Task {
            let updated = await PriceCheckService.shared.checkPrice(for: product)
            await MainActor.run {
                product = updated
                viewModel.loadProducts()
                isCheckingPrice = false
            }
        }
    }

    private func save() {
        isSaving = true
        var updated = product
        updated.name = name.isEmpty ? nil : name
        updated.targetPrice = Double(targetPrice.replacingOccurrences(of: ",", with: ".")) ?? product.targetPrice
        updated.alertEnabled = alertEnabled
        updated.alertPrice = alertEnabled
            ? Double(alertPrice.replacingOccurrences(of: ",", with: "."))
            : nil

        LocalStorageService.shared.updateProduct(updated)
        product = updated
        viewModel.loadProducts()
        viewModel.successMessage = "Ürün güncellendi"
        isSaving = false
    }
}
