import SwiftUI
import UIKit

struct ProductsView: View {
    @StateObject private var viewModel = ProductsViewModel()
    @ObservedObject private var premiumStore = PremiumStoreService.shared
    @State private var showAddProduct = false
    @State private var showProductLimitAlert = false

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

                if !premiumStore.isPremium {
                    BannerAdView()
                        .frame(height: 50)
                        .background(Color(.systemBackground))
                }
            }
            .navigationTitle("TagTrack")
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
            .alert("Ürün Limiti", isPresented: $showProductLimitAlert) {
                Button("Tamam", role: .cancel) {}
            } message: {
                Text("Ücretsiz planda en fazla \(PremiumStoreService.freeProductLimit) ürün ekleyebilirsiniz. Premium ile sınırsız takip edin.")
            }
        }
    }

    private func handleAddTapped() {
        guard premiumStore.canAddMoreProducts else {
            showProductLimitAlert = true
            return
        }

        if premiumStore.isPremium {
            showAddProduct = true
            return
        }

        guard let vc = UIApplication.shared.rootViewController else {
            showAddProduct = true
            return
        }
        AdService.shared.showRewarded(
            from: vc,
            onRewarded: { showAddProduct = true },
            onSkipped: { showAddProduct = true }
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
