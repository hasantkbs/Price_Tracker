import SwiftUI

// ─────────────────────────────────────────────────────────────────────────────
// MARK: - SplashView
// ─────────────────────────────────────────────────────────────────────────────
// TODO LOGO — SplashView
//   1. Assets.xcassets içine "AppLogo" adıyla PNG/SVG logonuzu ekleyin.
//   2. "AppLogo" adı yoksa gradient ikon fallback gösterilir.
//   3. Logonuzun arka planı şeffaf (alpha) olmalı, 1024×1024 px tavsiye edilir.
// ─────────────────────────────────────────────────────────────────────────────

struct SplashView: View {

    // Animasyon durumları
    @State private var logoScale:   CGFloat = 0.55
    @State private var logoOpacity: Double  = 0
    @State private var logoY:       CGFloat = 20
    @State private var taglineOpacity: Double = 0
    @State private var ringScale:   CGFloat = 0.6
    @State private var ringOpacity: Double  = 0

    var body: some View {
        ZStack {
            // Arka plan rengi – LaunchScreen ile aynı
            Color(.systemBackground).ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                // ── Logo alanı ──────────────────────────────────────────────
                ZStack {
                    // Pulse halkası
                    Circle()
                        .stroke(
                            LinearGradient(
                                colors: [Color.blue.opacity(0.35), Color.purple.opacity(0.15)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 2
                        )
                        .frame(width: 148, height: 148)
                        .scaleEffect(ringScale)
                        .opacity(ringOpacity)

                    // TODO LOGO — "AppLogo" görselini Assets.xcassets'e ekleyin
                    if UIImage(named: "AppLogo") != nil {
                        Image("AppLogo")
                            .resizable()
                            .scaledToFit()
                            .frame(width: 110, height: 110)
                            .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
                            .shadow(color: .black.opacity(0.15), radius: 16, x: 0, y: 6)
                    } else {
                        // Fallback – logonuzu ekleyene kadar görünür
                        ZStack {
                            RoundedRectangle(cornerRadius: 24, style: .continuous)
                                .fill(
                                    LinearGradient(
                                        colors: [Color(hex: "1C6EFF"), Color(hex: "8A2BE2")],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .frame(width: 110, height: 110)
                                .shadow(color: Color(hex: "1C6EFF").opacity(0.4), radius: 18, x: 0, y: 8)

                            Image(systemName: "tag.fill")
                                .font(.system(size: 46, weight: .semibold))
                                .foregroundColor(.white)
                        }
                    }
                }
                .scaleEffect(logoScale)
                .opacity(logoOpacity)
                .offset(y: logoY)

                // ── Uygulama adı & tagline ───────────────────────────────────
                VStack(spacing: 6) {
                    // TODO LOGO — Buraya metin logonuzu veya wordmark görselinizi koyabilirsiniz
                    Text("Fiyat Takibi")
                        .font(.system(size: 26, weight: .bold, design: .rounded))
                        .foregroundColor(.primary)

                    Text("by Algorix")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.secondary)
                        .tracking(1.5)
                        .textCase(.uppercase)
                }
                .padding(.top, 22)
                .opacity(taglineOpacity)

                Spacer()

                // Alt boşluk
                Color.clear.frame(height: 60)
            }
        }
        .onAppear { runAnimation() }
    }

    // MARK: - Animasyon sekansı

    private func runAnimation() {
        // 1. Logo fade-in + yükseli
        withAnimation(.spring(response: 0.65, dampingFraction: 0.7)) {
            logoScale   = 1.0
            logoOpacity = 1.0
            logoY       = 0
        }

        // 2. Pulse halkası
        withAnimation(.easeOut(duration: 0.6).delay(0.25)) {
            ringScale   = 1.35
            ringOpacity = 0.8
        }
        withAnimation(.easeIn(duration: 0.5).delay(0.75)) {
            ringScale   = 1.7
            ringOpacity = 0
        }

        // 3. Tagline
        withAnimation(.easeOut(duration: 0.45).delay(0.5)) {
            taglineOpacity = 1.0
        }
    }
}

// ─── Hex renk yardımcısı ────────────────────────────────────────────────────
private extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: .alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let r = Double((int >> 16) & 0xFF) / 255
        let g = Double((int >> 8)  & 0xFF) / 255
        let b = Double( int        & 0xFF) / 255
        self.init(red: r, green: g, blue: b)
    }
}
