import SwiftUI

struct PrivacyPolicyView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Gizlilik Politikası")
                    .font(.title).bold()
                
                Text("Son Güncelleme: 4 Haziran 2026")
                    .font(.caption).foregroundColor(.secondary)
                
                Group {
                    Text("1. Veri Toplama")
                        .font(.headline)
                    Text("TagTrack, sadece takip ettiğiniz ürünlerin linklerini ve fiyat geçmişini yerel olarak cihazınızda veya kendi sunucumuzda saklar. Kişisel verileriniz izniniz olmadan üçüncü taraflarla paylaşılmaz.")
                    
                    Text("2. Reklamlar")
                        .font(.headline)
                    Text("Uygulama, reklam göstermek için Google AdMob kullanır. AdMob, size daha ilgi çekici reklamlar sunmak için cihaz tanımlayıcılarını kullanabilir.")
                    
                    Text("3. İletişim")
                        .font(.headline)
                    Text("Gizlilik politikamız hakkında sorularınız için uygulama üzerinden bizimle iletişime geçebilirsiniz.")
                }
                
                Spacer()
            }
            .padding()
        }
        .navigationTitle("Gizlilik Politikası")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct TermsOfServiceView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("Kullanım Şartları")
                    .font(.title).bold()
                
                Text("Son Güncelleme: 4 Haziran 2026")
                    .font(.caption).foregroundColor(.secondary)
                
                Group {
                    Text("1. Hizmet Kullanımı")
                        .font(.headline)
                    Text("TagTrack, e-ticaret sitelerindeki fiyatları takip etmenize yardımcı olan bir araçtır. Fiyatların doğruluğu veya güncelliği konusunda garanti verilmez.")
                    
                    Text("2. Abonelikler")
                        .font(.headline)
                    Text("Premium abonelikler reklamsız deneyim ve ek özellikler sunar. İptal işlemleri App Store üzerinden yapılmalıdır.")
                    
                    Text("3. Sorumluluk Reddi")
                        .font(.headline)
                    Text("Uygulamanın kullanımından doğabilecek herhangi bir maddi kayıptan TagTrack sorumlu tutulamaz.")
                }
                
                Spacer()
            }
            .padding()
        }
        .navigationTitle("Kullanım Şartları")
        .navigationBarTitleDisplayMode(.inline)
    }
}
