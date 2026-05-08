import SwiftUI

struct ProductsView: View {
    @StateObject private var viewModel = ProductsViewModel()
    @State private var showAddProduct = false
    @State private var showRewardedGate = false

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // ── Ürün listesi ────────────────────────────────────────────
                Group {
                    if viewModel.products.isEmpty {
                        EmptyProductsView()
                    } else {
                        productList
                    }
                }

                // TODO LOGO — Navigasyon çubuğu başlığına logo eklemek isterseniz
                //             .toolbar içinde ToolbarItem(placement: .principal) kullanın.

                // ── Banner reklam (alt sabit) ───────────────────────────────
                // TODO ADS — Reklam birim ID'sini ayarladıktan sonra bu bölüm canlıya geçer
                BannerAdView()
                    .frame(height: 50)
                    .background(Color(.systemBackground))
            }
            .navigationTitle("Fiyat Takibi")
            // TODO LOGO — Büyük başlığı gizleyip logo koymak için:
            //   .navigationBarTitleDisplayMode(.inline)
            //   + ToolbarItem(placement: .principal) { Image("AppLogo")... }
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: handleAddTapped) {
                        Image(systemName: "plus")
                            .font(.title3)
                    }
                }
                ToolbarItem(placement: .navigationBarLeading) {
                    if viewModel.isLoading {
                        ProgressView().scaleEffect(0.8)
                    }
                }
            }
            .sheet(isPresented: $showAddProduct) {
                AddProductView { viewModel.loadProducts() }
            }
            .alert("Hata", isPresented: Binding(
                get: { viewModel.errorMessage != nil },
                set: { if !$0 { viewModel.clearError() } }
            )) {
                Button("Tamam") { viewModel.clearError() }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
            .onAppear { viewModel.loadProducts() }
            .refreshable { await viewModel.checkAllPrices() }
        }
    }

    // MARK: - Ürün ekleme – rewarded reklam kapısı

    private func handleAddTapped() {
        guard let vc = UIApplication.shared.rootViewController else {
            showAddProduct = true
            return
        }
        // Rewarded reklam hazırsa göster; ödül → ürün ekleme ekranını aç
        // Hazır değilse direkt aç (kullanıcıyı engelleme)
        AdService.shared.showRewarded(
            from: vc,
            onRewarded: { showAddProduct = true },
            onSkipped:  { showAddProduct = true }   // skip'te de aç (UX kararı)
        )
    }

    // MARK: - Liste

    private var productList: some View {
        List {
            ForEach(viewModel.products) { product in
                NavigationLink(destination: EditProductView(product: product, viewModel: viewModel)) {
                    ProductRowView(product: product)
                }
                .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                    Button(role: .destructive) {
                        viewModel.deleteProduct(id: product.id)
                    } label: {
                        Label("Sil", systemImage: "trash")
                    }
                }
                .swipeActions(edge: .leading, allowsFullSwipe: false) {
                    Button {
                        Task { await viewModel.checkPrice(for: product) }
                    } label: {
                        Label("Kontrol Et", systemImage: "arrow.clockwise")
                    }
                    .tint(.blue)
                }
            }
        }
        .listStyle(.insetGrouped)
    }
}

// MARK: - Boş durum

struct EmptyProductsView: View {
    var body: some View {
        VStack(spacing: 16) {
            // TODO LOGO — Boş durum ikonunu logonuzla değiştirebilirsiniz
            Image(systemName: "tag.slash.fill")
                .font(.system(size: 56))
                .foregroundColor(.secondary.opacity(0.4))
            Text("Takip Edilen Ürün Yok")
                .font(.title3).fontWeight(.semibold)
                .foregroundColor(.secondary)
            Text("Sağ üstteki + butonuna basarak\nbir ürün ekleyin.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
