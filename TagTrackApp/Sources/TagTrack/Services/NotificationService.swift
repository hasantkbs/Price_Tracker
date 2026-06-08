import UserNotifications

class NotificationService {
    static let shared = NotificationService()
    private init() {}

    func requestPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { _, _ in }
    }

    func scheduleAlert(for product: Product, currentPrice: Double) {
        guard product.isAlertEnabled,
              let alertPrice = product.alertPrice,
              currentPrice <= alertPrice else { return }

        let content = UNMutableNotificationContent()
        content.title = "Fiyat Alarmı!"
        content.body = "\(product.displayName): \(formatPrice(currentPrice)) — hedef fiyatın altına düştü!"
        content.sound = .default

        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 1, repeats: false)
        let request = UNNotificationRequest(
            identifier: "price-alert-\(product.id)-\(Int(Date().timeIntervalSince1970))",
            content: content,
            trigger: trigger
        )
        UNUserNotificationCenter.current().add(request) { _ in }
    }

    private func formatPrice(_ price: Double) -> String {
        String(format: "%.2f ₺", price)
    }
}
