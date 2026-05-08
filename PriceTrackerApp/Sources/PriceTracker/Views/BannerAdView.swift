import SwiftUI
import GoogleMobileAds

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - BannerAdView
// ─────────────────────────────────────────────────────────────────────────────
// Kullanım:
//   BannerAdView()
//     .frame(height: 50)
//
// TODO ADS — AdService.AdUnitID.banner değerini gerçek reklam birimi ID'nizle
//            değiştirdiğinizde bu view otomatik çalışır.
// ─────────────────────────────────────────────────────────────────────────────

struct BannerAdView: UIViewRepresentable {
    func makeUIView(context: Context) -> GADBannerView {
        let banner = GADBannerView(adSize: GADAdSizeBanner)
        banner.adUnitID = AdService.shared.bannerAdUnitID
        banner.rootViewController = UIApplication.shared.rootViewController
        banner.load(GADRequest())
        return banner
    }

    func updateUIView(_ uiView: GADBannerView, context: Context) {}
}
