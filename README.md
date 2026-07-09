# Fırsat Paylaş Kazan - Telegram Taslak Botu

Ürün linki + açıklama gönderdiğinde otomatik olarak görselli, düzenli bir
paylaşım taslağı hazırlayan; onayından sonra kanala gönderen Telegram botu.

## Nasıl Çalışır?

1. Bota (özel mesajdan) sadece ürün linkini gönderirsin (istersen fiyatı da
   ekleyebilirsin, eklemesen de olur):
   ```
   https://www.trendyol.com/urun-linki
   ```
   veya fiyatı sayfada bulamazsa diye elle de yazabilirsin:
   ```
   https://www.trendyol.com/urun-linki 199 TL
   ```
2. Bot linke gidip ürün görselini, başlığını ve **açıklamasını** otomatik
   çeker (Open Graph verisi), metinde veya sayfada geçen fiyatı yakalar.
   Açıklamayı senin yazman gerekmez, bot ürün sayfasındaki önemli
   bilgilerden kendisi oluşturur.
3. Sana görselli, düzenli formatlanmış bir **taslak önizleme** gönderir:
   - ✅ Kanala Gönder
   - ❌ İptal
   - ✏️ Metni Düzenle
4. "Kanala Gönder" dediğinde taslak otomatik olarak kanalına paylaşılır.

> Not: Bazı siteler botlara görsel vermeyebilir (bot koruması). Böyle
> durumlarda taslak görselsiz gelir, sen manuel görsel ekleyebilir ya da
> metni düzenleyip yine de gönderebilirsin.

## Kurulum

### 1) Bot oluştur
- Telegram'da **@BotFather**'a git, `/newbot` yaz, adımları takip et.
- Sana bir **token** verecek (`BOT_TOKEN`).

### 2) Botu kanala admin yap
- Kanalını aç → Kanal Ayarları → Yöneticiler → botunu ekle → mesaj
  gönderme yetkisi ver.

### 3) Kanal ID'sini bul
- Kanal kullanıcı adın varsa direkt `@kanaladi` kullanabilirsin.
- Kullanıcı adı yoksa: kanaldan bir mesajı **@userinfobot**'a forward et,
  sana `-100...` ile başlayan kanal ID'sini verir.

### 4) Kendi Telegram ID'ni öğren
- **@userinfobot**'a `/start` yaz, sana kendi ID'ni verir. Bu ID'yi
  `ADMIN_IDS` içine ekle (botu sadece sen/belirlediğin kişiler kullanabilsin
  diye).

### 5) Ortam değişkenlerini ayarla
`.env.example` dosyasını `.env` olarak kopyala ve içini doldur:
```
BOT_TOKEN=...
CHANNEL_ID=...
ADMIN_IDS=...
```

### 6) Kur ve çalıştır
```bash
pip install -r requirements.txt
python bot.py
```

## 7/24 Çalıştırma

Bu bot `python bot.py` ile çalıştığın sürece aktif kalır (polling
yöntemi). Bilgisayarını kapattığında durur. Sürekli açık kalması için
küçük bir sunucuya (Railway, Render, bir VPS, Raspberry Pi vb.) deploy
etmen gerekir. İstersen bu adımda da yardımcı olabilirim — hangi platformu
kullanmak istediğini söylemen yeterli.

## Metni ve formatı özelleştirme

`bot.py` içindeki `FOOTER` değişkenini ve `build_caption()` fonksiyonunu
değiştirerek taslağın görünümünü (emoji, başlık, hashtag'ler vb.)
dilediğin gibi ayarlayabilirsin.
