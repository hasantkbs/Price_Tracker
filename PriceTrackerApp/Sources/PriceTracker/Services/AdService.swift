import Foundation
import GoogleMobileAds
import UIKit

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - AdService
// ─────────────────────────────────────────────────────────────────────────────
// Gelir modeli:
//   • Banner      → ProductsView alt kısmında sabit banner
//   • Rewarded    → Kullanıcı ürün eklemek istediğinde izleme opsiyonlu rewarded
//   • Interstitial→ Belirli sayıda uygulama açılışında otomatik interstitial
//
// TODO ADS — Adım 1: admob.google.com'da uygulama ve reklam birimleri oluşturun,
//            ardından aşağıdaki AdUnitID değerlerini gerçek ID'lerle değiştirin.
// ─────────────────────────────────────────────────────────────────────────────

@MainActor
class AdService: NSObject, ObservableObject {
    static let shared = AdService()

    // ── Reklam Birimi ID'leri ─────────────────────────────────────────────
    // TODO ADS — Test ID'leri – production'a almadan önce gerçek ID'lerle değiştirin
    enum AdUnitID {
        /// Banner reklam birimi
        static let banner       = "ca-app-pub-3940256099942544/2934735716"  // TODO ADS
        /// Rewarded reklam birimi (ürün ekleme)
        static let rewarded     = "ca-app-pub-3940256099942544/1712485313"  // TODO ADS
        /// Interstitial reklam birimi (periyodik açılış)
        static let interstitial = "ca-app-pub-3940256099942544/4411468910"  // TODO ADS
    }

    // ── State ─────────────────────────────────────────────────────────────
    @Published var rewardedAdReady     = false
    @Published var interstitialAdReady = false

    private var rewardedAd:     GADRewardedAd?
    private var interstitialAd: GADInterstitialAd?

    private var openCount: Int {
        get { UserDefaults.standard.integer(forKey: "adOpenCount") }
        set { UserDefaults.standard.set(newValue, forKey: "adOpenCount") }
    }

    // Kaç açılışta bir interstitial gösterilsin (0 = kapalı)
    private let interstitialEvery = 4

    // MARK: - Init

    override private init() {
        super.init()
    }

    // MARK: - Banner ID (BannerAdView tarafından kullanılır)

    var bannerAdUnitID: String { AdUnitID.banner }

    // MARK: - Preload

    func preloadAll() {
        loadRewarded()
        loadInterstitial()
    }

    // MARK: - Rewarded Ad

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

    /// Rewarded reklamı göster.
    /// - onRewarded: Kullanıcı ödülü kazandığında → ürün ekleme izni
    /// - onSkipped:  Kullanıcı atladığında çağrılır
    func showRewarded(
        from viewController: UIViewController,
        onRewarded: @escaping () -> Void,
        onSkipped:  @escaping () -> Void
    ) {
        guard let ad = rewardedAd else {
            onRewarded() // Reklam hazır değilse direkt geç
            loadRewarded()
            return
        }
        rewardedAd = nil
        rewardedAdReady = false

        ad.present(fromRootViewController: viewController) {
            DispatchQueue.main.async { onRewarded() }
        }
        // Delegate üzerinden atlanma tespiti için basit fallback
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { [weak self] in
            self?.loadRewarded()
        }
    }

    // MARK: - Interstitial Ad

    private func loadInterstitial() {
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

    /// Her uygulama açılışında çağrılır; belirli sayıda açılışta interstitial gösterir.
    func handleAppLaunch(from viewController: UIViewController) {
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

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - UIApplication yardımcısı
// ─────────────────────────────────────────────────────────────────────────────
extension UIApplication {
    var rootViewController: UIViewController? {
        connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first { $0.isKeyWindow }?
            .rootViewController
    }
}
