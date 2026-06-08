import SwiftUI
import GoogleMobileAds

@main
struct TagTrackApp: App {
    @State private var showSplash = true
    @Environment(\.scenePhase) private var scenePhase

    init() {
        BackgroundPriceCheckService.shared.register()
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
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.2) {
                    showSplash = false
                }
            }
            .task {
                await PremiumStoreService.shared.loadProducts()
            }
        }
        .onChange(of: scenePhase) { phase in
            switch phase {
            case .active:
                TrackingAuthorizationService.requestIfNeeded()
                BackgroundPriceCheckService.shared.scheduleNextCheck()
                Task { await PriceCheckService.shared.checkAllPrices() }
                if let vc = UIApplication.shared.rootViewController {
                    AdService.shared.handleAppLaunch(from: vc)
                }
            default:
                break
            }
        }
    }
}
