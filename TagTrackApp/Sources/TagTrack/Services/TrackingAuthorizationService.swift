import AppTrackingTransparency

enum TrackingAuthorizationService {
    /// AdMob kişiselleştirilmiş reklamlar için ATT izni (yalnızca henüz belirlenmemişse).
    static func requestIfNeeded() {
        guard #available(iOS 14, *) else { return }
        guard ATTrackingManager.trackingAuthorizationStatus == .notDetermined else { return }
        ATTrackingManager.requestTrackingAuthorization { _ in }
    }
}
