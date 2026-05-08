import Foundation

class SettingsViewModel: ObservableObject {
    @Published var checkIntervalHours: Int {
        didSet { UserDefaults.standard.set(checkIntervalHours, forKey: "checkIntervalHours") }
    }

    @Published var notificationsEnabled: Bool {
        didSet { UserDefaults.standard.set(notificationsEnabled, forKey: "notificationsEnabled") }
    }

    init() {
        let savedInterval = UserDefaults.standard.integer(forKey: "checkIntervalHours")
        self.checkIntervalHours = savedInterval > 0 ? savedInterval : 6
        self.notificationsEnabled = UserDefaults.standard.bool(forKey: "notificationsEnabled")
    }
}
