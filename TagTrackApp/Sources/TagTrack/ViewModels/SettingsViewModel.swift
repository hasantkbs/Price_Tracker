import Foundation

class SettingsViewModel: ObservableObject {
    @Published var checkIntervalHours: Int {
        didSet {
            UserDefaults.standard.set(checkIntervalHours, forKey: "checkIntervalHours")
            BackgroundPriceCheckService.shared.scheduleNextCheck()
        }
    }

    @Published var notificationsEnabled: Bool {
        didSet { UserDefaults.standard.set(notificationsEnabled, forKey: "notificationsEnabled") }
    }

    @Published var showDeleteDataConfirm = false

    init() {
        let savedInterval = UserDefaults.standard.integer(forKey: "checkIntervalHours")
        self.checkIntervalHours = savedInterval > 0 ? savedInterval : 6
        self.notificationsEnabled = UserDefaults.standard.bool(forKey: "notificationsEnabled")
    }

    func deleteAllUserData() {
        LocalStorageService.shared.deleteAllProducts()
        UserDefaults.standard.removeObject(forKey: "checkIntervalHours")
        UserDefaults.standard.removeObject(forKey: "notificationsEnabled")
        UserDefaults.standard.removeObject(forKey: "adOpenCount")
        checkIntervalHours = 6
        notificationsEnabled = false
    }
}
