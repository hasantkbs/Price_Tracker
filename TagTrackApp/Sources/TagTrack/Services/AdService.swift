import Foundation
import GoogleMobileAds
import UIKit

@MainActor
class AdService: NSObject, ObservableObject {
    static let shared = AdService()

    private enum TestAdUnitID {
        static let publisherPrefix = "3940256099942544"
        static let banner       = "ca-app-pub-3940256099942544/2934735716"
        static let rewarded     = "ca-app-pub-3940256099942544/1712485313"
        static let interstitial = "ca-app-pub-3940256099942544/4411468910"
    }

    /// Release'te henüz production interstitial yoksa Google test birimi yüklenmesin.
    private var interstitialAdsEnabled: Bool {
        !AdUnitID.interstitial.contains(TestAdUnitID.publisherPrefix)
    }

    enum AdUnitID {
        static var banner: String { resolvedPlistID("GADBannerAdUnitID", fallback: TestAdUnitID.banner) }
        static var rewarded: String { resolvedPlistID("GADRewardedAdUnitID", fallback: TestAdUnitID.rewarded) }
        static var interstitial: String { resolvedPlistID("GADInterstitialAdUnitID", fallback: TestAdUnitID.interstitial) }

        private static func resolvedPlistID(_ key: String, fallback: String) -> String {
            let value = Bundle.main.object(forInfoDictionaryKey: key) as? String
            guard let value, !value.isEmpty, !value.hasPrefix("$(") else { return fallback }
            return value
        }
    }

    @Published var rewardedAdReady     = false
    @Published var interstitialAdReady = false

    private var rewardedAd:     GADRewardedAd?
    private var interstitialAd: GADInterstitialAd?

    private var openCount: Int {
        get { UserDefaults.standard.integer(forKey: "adOpenCount") }
        set { UserDefaults.standard.set(newValue, forKey: "adOpenCount") }
    }

    private let interstitialEvery = 4

    override private init() {
        super.init()
    }

    var bannerAdUnitID: String { AdUnitID.banner }

    func preloadAll() {
        loadRewarded()
        if interstitialAdsEnabled { loadInterstitial() }
    }

    private func loadRewarded() {
        GADRewardedAd.load(
            withAdUnitID: AdUnitID.rewarded,
            request: GADRequest()
        ) { [weak self] ad, _ in
            guard let self else { return }
            Task { @MainActor in
                self.rewardedAd = ad
                self.rewardedAdReady = ad != nil
            }
        }
    }

    func showRewarded(
        from viewController: UIViewController,
        onRewarded: @escaping () -> Void,
        onSkipped:  @escaping () -> Void
    ) {
        guard let ad = rewardedAd else {
            onRewarded()
            loadRewarded()
            return
        }
        rewardedAd = nil
        rewardedAdReady = false

        ad.present(fromRootViewController: viewController) {
            DispatchQueue.main.async { onRewarded() }
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { [weak self] in
            self?.loadRewarded()
        }
    }

    private func loadInterstitial() {
        guard interstitialAdsEnabled else { return }
        GADInterstitialAd.load(
            withAdUnitID: AdUnitID.interstitial,
            request: GADRequest()
        ) { [weak self] ad, _ in
            guard let self else { return }
            Task { @MainActor in
                self.interstitialAd = ad
                self.interstitialAdReady = ad != nil
            }
        }
    }

    func handleAppLaunch(from viewController: UIViewController) {
        guard interstitialAdsEnabled else { return }
        guard !PremiumStoreService.shared.isPremium else { return }
        openCount += 1
        guard interstitialEvery > 0,
              openCount % interstitialEvery == 0,
              let ad = interstitialAd else { return }

        ad.present(fromRootViewController: viewController)
        interstitialAd = nil
        interstitialAdReady = false
        loadInterstitial()
    }
}

extension UIApplication {
    var rootViewController: UIViewController? {
        connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first { $0.isKeyWindow }?
            .rootViewController
    }
}
