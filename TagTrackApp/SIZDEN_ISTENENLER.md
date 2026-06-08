# TagTrack — App Store Hazırlık Listesi (Kalan İşler)

Bu liste, uygulamanın markete gönderilmesi için **sizin tarafınızdan** yapılması gereken teknik ve idari adımları içerir. Yapılanları listeden silebilir veya işaretleyebilirsiniz.

## 1. Apple Geliştirici Hesabı ve Kurulum
- [ ] **Apple Developer Program** üyeliğini başlatın (Yıllık 99$).
- [ ] **App Store Connect** üzerinden yeni uygulama oluşturun:
    - İsim: `TagTrack`
    - Bundle ID: `com.tagtrack.app`
- [ ] **IAP (Uygulama İçi Satın Alma)** ürününü oluşturun:
    - ID: `com.tagtrack.app.premium`
    - Tip: Non-Consumable (Kalıcı)
- [ ] **AdMob Interstitial ID:** AdMob panelinden "Geçiş Reklamı" birimi oluşturun ve ID'yi bana iletin veya `project.yml` içinde güncelleyin.

## 2. Test ve Onay Süreci
- [ ] **Sandbox Testi:** Apple Developer hesabı bağlandıktan sonra Premium satın alma akışını "Sandbox" hesabı ile test edin.
- [ ] **Test Ürünü:** Apple inceleme ekibinin (Reviewer) test edebilmesi için aktif çalışan bir ürün URL'si (Trendyol, Hepsiburada vb.) belirleyin.

## 3. Görsel ve Metin Hazırlığı
- [ ] **Ekran Görüntüleri (Screenshots):** iPhone 15 Pro Max (6.7") ve iPhone 13 Pro (6.5") boyutlarında en az 3'er adet ekran görüntüsü hazırlayın.
- [ ] **Tanıtım Metni:** Uygulamanın ne yaptığını anlatan kısa ve ilgi çekici bir açıklama yazın.

## 4. Yayınlama Öncesi Son Kontrol
- [ ] **Sertifikalar:** Apple Distribution sertifikası ve Provisioning Profile oluşturulması (Xcode üzerinden otomatik yapılabilir).
- [ ] **Arşiv:** Xcode'da `Product > Archive` yaparak uygulamayı App Store Connect'e gönderin.

---

**Tamamlananlar (Arşiv):**
- [x] Uygulama ismi **TagTrack** olarak güncellendi.
- [x] Bundle ID ve proje mimarisi yeni isme göre düzenlendi.
- [x] İkon ve Logo setleri (TagTrackIcon / TagTrackLogo) yapılandırıldı.
- [x] Gizlilik Politikası ve Kullanım Şartları uygulama içine (local) eklendi.
- [x] Açılış ekranı (Splash) ve ana sayfa görsel düzenlemeleri yapıldı.
- [x] AdMob Banner ve Rewarded (Ödüllü) reklam entegrasyonu tamamlandı.
