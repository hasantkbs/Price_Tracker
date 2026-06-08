import BackgroundTasks
import Foundation

/// BGTaskScheduler ile periyodik fiyat kontrolü (Info.plist background modes ile eşleşir).
final class BackgroundPriceCheckService {
    static let shared = BackgroundPriceCheckService()
    static let taskIdentifier = "com.tagtrack.app.pricecheck"

    private init() {}

    func register() {
        BGTaskScheduler.shared.register(
            forTaskWithIdentifier: Self.taskIdentifier,
            using: nil
        ) { task in
            guard let refreshTask = task as? BGAppRefreshTask else {
                task.setTaskCompleted(success: false)
                return
            }
            self.handleAppRefresh(task: refreshTask)
        }
    }

    func scheduleNextCheck() {
        let hours = UserDefaults.standard.integer(forKey: "checkIntervalHours")
        let intervalHours = hours > 0 ? hours : 6

        let request = BGAppRefreshTaskRequest(identifier: Self.taskIdentifier)
        request.earliestBeginDate = Date(timeIntervalSinceNow: Double(intervalHours) * 3600)

        do {
            try BGTaskScheduler.shared.submit(request)
        } catch {
            // Simulator veya background refresh kapalıysa sessizce atlanır
        }
    }

    private func handleAppRefresh(task: BGAppRefreshTask) {
        scheduleNextCheck()

        let work = Task {
            await PriceCheckService.shared.checkAllPrices()
            task.setTaskCompleted(success: true)
        }

        task.expirationHandler = {
            work.cancel()
            task.setTaskCompleted(success: false)
        }
    }
}
