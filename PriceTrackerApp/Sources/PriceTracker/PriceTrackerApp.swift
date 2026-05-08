import SwiftUI
import GoogleMobileAds

@main
struct PriceTrackerApp: App {
    @State private var showSplash = true
    @Environment(\.scenePhase) private var scenePhase

    // ── AdMob başlatma ─────────────────────────────────────────────────────
    init() {
        GADMobileAds.sharedInstance().start { _ in
            Task { @MainActor in
                AdService.shared.preloadAll()
            }
        }
    }

    var body: some Scene {
        WindowGroup {
            ZStack {
                if showSplash {
                    SplashView()
                        .transition(.opacity)
                } else {
                    ContentView()
                        .transition(.opacity)
                }
            }
            .animation(.easeInOut(duration: 0.45), value: showSplash)
            .onAppear {
                NotificationService.shared.requestPermission()
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.2) {
                    showSplash = false
                }
            }
        }
        .onChange(of: scenePhase) { phase in
            if phase == .active {
                Task { await PriceCheckService.shared.checkAllPrices() }
                if let vc = UIApplication.shared.rootViewController {
                    AdService.shared.handleAppLaunch(from: vc)
                }
            }
        }
    }
}
