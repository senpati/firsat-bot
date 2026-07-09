# Railway'e Deploy Etme

## 1) Kodu GitHub'a yükle
1. GitHub'da yeni bir repo oluştur (örn. `firsat-bot`), **private** yapabilirsin.
2. Bu klasördeki dosyaları (`bot.py`, `requirements.txt`, `Procfile`,
   `.gitignore`, `README.md`) o repoya yükle.
   - `.env` dosyanı **asla** repoya yükleme, `.gitignore` zaten onu engeller.

En kolay yol: GitHub Desktop kullanmıyorsan, GitHub'ın web arayüzünden
"Add file → Upload files" ile dosyaları sürükleyip commit edebilirsin.

## 2) Railway'de proje oluştur
1. https://railway.app adresine git, GitHub hesabınla giriş yap.
2. **New Project → Deploy from GitHub repo** seç.
3. Az önce oluşturduğun `firsat-bot` reposunu seç.
4. Railway otomatik olarak `requirements.txt`'i görüp Python ortamı kuracak
   ve `Procfile`'daki komutu (`python bot.py`) çalıştıracak.

## 3) Ortam değişkenlerini gir
Proje sayfasında **Variables** sekmesine git ve şunları ekle:

| Değişken | Değer |
|---|---|
| `BOT_TOKEN` | BotFather'dan aldığın token |
| `CHANNEL_ID` | `@kanaladi` veya `-100...` |
| `ADMIN_IDS` | Telegram ID'n (birden fazlaysa virgülle ayır) |

Kaydettiğinde Railway otomatik olarak yeniden deploy eder.

## 4) Kontrol et
- **Deployments** sekmesinden build'in başarılı olduğunu gör.
- **Logs** sekmesinde `Bot başlatıldı, mesajlar bekleniyor...` yazısını
  görüyorsan bot çalışıyor demektir.
- Telegram'dan bota bir ürün linki gönder, taslağın gelip gelmediğini test et.

## Notlar
- Bu bot bir web sunucusu değil, sürekli çalışan bir "worker" (polling)
  olarak çalışır. Railway'in ücretsiz planı bunun için yeterlidir, ekstra
  port ayarı yapmana gerek yok.
- Kod üzerinde değişiklik yapıp GitHub'a tekrar push ettiğinde Railway
  otomatik olarak yeni versiyonu deploy eder.
- Railway'in ücretsiz kotası dolarsa bot durabilir; kullanım yoğunluğuna
  göre küçük bir ücretli plana geçmen gerekebilir.
