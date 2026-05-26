import SwiftUI

struct SettingsView: View {
    @StateObject private var settingsVM = SettingsViewModel()

    private let intervalOptions = [1, 3, 6, 12, 24]

    var body: some View {
        NavigationView {
            Form {
                notificationSection
                checkIntervalSection
                aboutSection
            }
            .navigationTitle("Ayarlar")
        }
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
            footer: Text("Uygulama ön plana geçtiğinde tüm ürünler kontrol edilir. Bu ayar otomatik arka plan kontrolü içindir.")
        ) {
            Picker("Kontrol Aralığı", selection: $settingsVM.checkIntervalHours) {
                ForEach(intervalOptions, id: \.self) { hour in
                    Text("\(hour) saat").tag(hour)
                }
            }
        }
    }

    private var aboutSection: some View {
        Section(header: Text("Hakkında")) {
            HStack {
                Text("Uygulama Versiyonu")
                Spacer()
                Text(Bundle.main.infoDictionary.flatMap { $0["CFBundleShortVersionString"] as? String } ?? "1.0.0").foregroundColor(.secondary)
            }
            HStack {
                Text("Geliştirici")
                Spacer()
                Text("Algorix").foregroundColor(.secondary)
            }
            Link(destination: URL(string: "https://algorix.com.tr/privacy")!) {
                Label("Gizlilik Politikası", systemImage: "hand.raised.fill")
            }
            Link(destination: URL(string: "https://algorix.com.tr/terms")!) {
                Label("Kullanım Şartları", systemImage: "doc.text.fill")
            }
        }
    }
}
