import SwiftUI

struct SettingsView: View {
    @StateObject private var settingsVM = SettingsViewModel()
    @ObservedObject private var premiumStore = PremiumStoreService.shared

    private let intervalOptions = [1, 3, 6, 12, 24]

    var body: some View {
        NavigationView {
            Form {
                premiumSection
                notificationSection
                checkIntervalSection
                dataSection
                aboutSection
            }
            .navigationTitle("Ayarlar")
            .alert("Tüm Verileri Sil", isPresented: $settingsVM.showDeleteDataConfirm) {
                Button("Sil", role: .destructive) { settingsVM.deleteAllUserData() }
                Button("İptal", role: .cancel) {}
            } message: {
                Text("Takip ettiğiniz tüm ürünler ve yerel ayarlar kalıcı olarak silinecek.")
            }
            .alert("Premium", isPresented: Binding(
                get: { premiumStore.purchaseError != nil },
                set: { if !$0 { premiumStore.purchaseError = nil } }
            )) {
                Button("Tamam") { premiumStore.purchaseError = nil }
            } message: {
                Text(premiumStore.purchaseError ?? "")
            }
        }
    }

    private var premiumSection: some View {
        Section(
            header: Text("Premium"),
            footer: Text(premiumFooterText)
        ) {
            if premiumStore.isPremium {
                Label("Premium aktif", systemImage: "crown.fill")
                    .foregroundColor(.orange)
            } else {
                if let product = premiumStore.premiumProduct {
                    Button {
                        Task { await premiumStore.purchase() }
                    } label: {
                        HStack {
                            Text("Premium'a Yükselt")
                            Spacer()
                            if premiumStore.isPurchasing {
                                ProgressView()
                            } else {
                                Text(product.displayPrice)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                    .disabled(premiumStore.isPurchasing)
                } else {
                    Text("Ücretsiz planda en fazla \(PremiumStoreService.freeProductLimit) ürün takip edebilirsiniz.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Button("Satın Almaları Geri Yükle") {
                    Task { await premiumStore.restorePurchases() }
                }
                .disabled(premiumStore.isPurchasing)
            }
        }
    }

    private var premiumFooterText: String {
        if premiumStore.isPremium {
            return "Reklamsız ve sınırsız ürün takibi."
        }
        return "Premium: reklamsız deneyim ve sınırsız ürün. App Store Connect'te \(PremiumStoreService.productID) ürününü oluşturmanız gerekir."
    }

    private var notificationSection: some View {
        Section(header: Text("Bildirimler")) {
            Toggle("Fiyat alarmı bildirimleri", isOn: $settingsVM.notificationsEnabled)
                .onChange(of: settingsVM.notificationsEnabled) { enabled in
                    if enabled {
                        NotificationService.shared.requestPermission()
                    }
                }

            if !settingsVM.notificationsEnabled {
                Text("Bildirimler kapalı. Fiyat alarmı çalışmayacak.")
                    .font(.caption)
                    .foregroundColor(.orange)
            }
        }
    }

    private var checkIntervalSection: some View {
        Section(
            header: Text("Kontrol Sıklığı"),
            footer: Text("Uygulama ön plana geçtiğinde tüm ürünler kontrol edilir. Arka plan kontrolü için bu aralık kullanılır.")
        ) {
            Picker("Kontrol Aralığı", selection: $settingsVM.checkIntervalHours) {
                ForEach(intervalOptions, id: \.self) { hour in
                    Text("\(hour) saat").tag(hour)
                }
            }
        }
    }

    private var dataSection: some View {
        Section(header: Text("Veri")) {
            Button(role: .destructive) {
                settingsVM.showDeleteDataConfirm = true
            } label: {
                Label("Tüm Verileri Sil", systemImage: "trash")
            }
        }
    }

    private var aboutSection: some View {
        Section(header: Text("Hakkında")) {
            HStack {
                Text("Uygulama Versiyonu")
                Spacer()
                Text(Bundle.main.infoDictionary.flatMap { $0["CFBundleShortVersionString"] as? String } ?? "1.0.0")
                    .foregroundColor(.secondary)
            }
            HStack {
                Text("Geliştirici")
                Spacer()
                Text("TagTrack").foregroundColor(.secondary)
            }
            NavigationLink(destination: PrivacyPolicyView()) {
                Label("Gizlilik Politikası", systemImage: "hand.raised.fill")
            }
            NavigationLink(destination: TermsOfServiceView()) {
                Label("Kullanım Şartları", systemImage: "doc.text.fill")
            }
        }
    }
}
