import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

# ------------------------------------------------------------------
# AYARLAR
# ------------------------------------------------------------------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # örn: @kanalim  veya  -1001234567890
ADMIN_IDS = [x.strip() for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Kanal alt bilgisi (dilersen değiştir)
FOOTER = "\n\n🛍️ Fırsat Paylaş Kazan\n#firsat #indirim #kampanya"

URL_REGEX = re.compile(r"(https?://\S+)")
PRICE_REGEX = re.compile(r"(\d+[.,]?\d*)\s*(TL|₺|TRY)", re.IGNORECASE)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# admin başına bekleyen taslakları tutuyoruz
# { admin_id: {"text": str, "link": str, "price": str|None, "image_url": str|None,
#              "preview_message_id": int, "awaiting_edit": bool} }
pending_drafts = {}


def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS


def extract_price(text: str) -> str | None:
    m = PRICE_REGEX.search(text)
    if m:
        return f"{m.group(1)} {m.group(2).upper()}"
    return None


def fetch_og_data(url: str) -> dict:
    """Linkten görsel/başlık çekmeye çalışır (Open Graph meta etiketleri)."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }
    result = {"image": None, "title": None, "description": None}
    try:
        session = requests.Session()
        # Kısa linkleri (ty.gl, bit.ly vb.) gerçek ürün linkine yönlendirmesini takip et
        resp = session.get(url, headers=headers, timeout=12, allow_redirects=True)
        resp.encoding = resp.apparent_encoding  # Türkçe karakterler bozulmasın

        soup = BeautifulSoup(resp.text, "html.parser")

        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            result["image"] = og_image["content"]

        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            result["title"] = og_title["content"].strip()
        elif soup.title:
            result["title"] = soup.title.get_text().strip()

        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            result["description"] = og_desc["content"].strip()
        else:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                result["description"] = meta_desc["content"].strip()

        # Bazı siteler bot isteklerine genel/şablon bir açıklama döndürür.
        # Bunu tespit edip, gerçek açıklama yerine boş bırakıyoruz ki
        # kullanıcının kendi notu (varsa) veya sadece başlık kullanılsın.
        generic_markers = ["hızlı kargo", "aynı gün kargo", "trend yolu"]
        if result["description"] and any(
            marker in result["description"].lower() for marker in generic_markers
        ):
            result["description"] = None

        # Ürün açıklamaları genelde çok uzun oluyor, taslağı şişirmesin diye kısaltıyoruz
        if result["description"] and len(result["description"]) > 300:
            result["description"] = result["description"][:300].rsplit(" ", 1)[0] + "..."

        logger.info(
            f"OG çekildi -> title:{bool(result['title'])} "
            f"image:{bool(result['image'])} desc:{bool(result['description'])} "
            f"status:{resp.status_code} final_url:{resp.url}"
        )
    except Exception as e:
        logger.warning(f"OG verisi çekilemedi ({url}): {e}")
    return result


def build_caption(
    user_text: str, link: str, price: str | None, title: str | None, description: str | None
) -> str:
    # Kullanıcının linkle birlikte yazdığı ekstra not (varsa) - linki ve fiyatı çıkarıyoruz
    extra_note = URL_REGEX.sub("", user_text).strip()
    if price:
        extra_note = PRICE_REGEX.sub("", extra_note).strip()

    # Açıklama önceliği: ürün sayfasından çekilen açıklama. Yoksa kullanıcının notu kullanılır.
    body_text = description or extra_note

    parts = []
    if title:
        parts.append(f"🛍️ {title}")
    if body_text:
        parts.append(f"\n{body_text}")
    # Kullanıcı hem sayfa açıklaması hem kendi notunu eklemek isterse, ikisi de gösterilir
    if description and extra_note and extra_note != body_text:
        parts.append(f"\n{extra_note}")
    if price:
        parts.append(f"\n💰 Fiyat: {price}")
    parts.append(f"\n🔗 Satın Al: {link}")
    parts.append(FOOTER)

    return "\n".join(parts)


def preview_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Kanala Gönder", callback_data="send"),
                InlineKeyboardButton("❌ İptal", callback_data="cancel"),
            ],
            [InlineKeyboardButton("✏️ Metni Düzenle", callback_data="edit")],
        ]
    )


# ------------------------------------------------------------------
# HANDLERLAR
# ------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merhaba! Bana link + açıklama içeren bir mesaj gönder, "
        "senin için otomatik görselli ve düzenli bir paylaşım taslağı hazırlayayım."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Bu botu kullanma yetkin yok.")
        return

    text = update.message.text or update.message.caption or ""

    # Düzenleme moduysa: gelen metni yeni taslak metni olarak al
    draft = pending_drafts.get(user.id)
    if draft and draft.get("awaiting_edit"):
        draft["text"] = text
        draft["awaiting_edit"] = False
        await send_preview(update, context, user.id)
        return

    url_match = URL_REGEX.search(text)
    if not url_match:
        await update.message.reply_text(
            "Mesajında bir link bulamadım. Lütfen ürün linkini de ekleyerek tekrar gönder."
        )
        return

    link = url_match.group(1)
    price = extract_price(text)

    await update.message.reply_text("⏳ Ürün bilgisi ve görsel alınıyor, biraz bekle...")

    og_data = fetch_og_data(link)

    # Fiyat mesajda yoksa, ürün sayfasının açıklamasında geçiyor olabilir
    if not price and og_data.get("description"):
        price = extract_price(og_data["description"])

    pending_drafts[user.id] = {
        "text": text,
        "link": link,
        "price": price,
        "image_url": og_data.get("image"),
        "title": og_data.get("title"),
        "description": og_data.get("description"),
        "awaiting_edit": False,
    }

    await send_preview(update, context, user.id)


async def send_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    draft = pending_drafts[user_id]
    caption = build_caption(draft["text"], draft["link"], draft["price"], draft["title"], draft["description"])

    chat_id = update.effective_chat.id

    if draft["image_url"]:
        msg = await context.bot.send_photo(
            chat_id=chat_id,
            photo=draft["image_url"],
            caption=caption,
            reply_markup=preview_keyboard(),
        )
    else:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "⚠️ Görsel otomatik bulunamadı.\n\n" + caption
            ),
            reply_markup=preview_keyboard(),
        )

    draft["preview_message_id"] = msg.message_id


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user

    if not is_admin(user.id):
        await query.answer("Yetkin yok.", show_alert=True)
        return

    draft = pending_drafts.get(user.id)
    if not draft:
        await query.answer("Aktif bir taslak bulunamadı.", show_alert=True)
        return

    action = query.data

    if action == "send":
        caption = build_caption(draft["text"], draft["link"], draft["price"], draft["title"], draft["description"])
        try:
            if draft["image_url"]:
                await context.bot.send_photo(
                    chat_id=CHANNEL_ID, photo=draft["image_url"], caption=caption
                )
            else:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=caption)
            await query.answer("Kanala gönderildi! ✅")
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception as e:
            logger.error(f"Kanala gönderilemedi: {e}")
            await query.answer("Gönderilemedi, botun kanalda admin olduğundan emin ol.", show_alert=True)
        finally:
            pending_drafts.pop(user.id, None)

    elif action == "cancel":
        await query.answer("İptal edildi.")
        await query.edit_message_reply_markup(reply_markup=None)
        pending_drafts.pop(user.id, None)

    elif action == "edit":
        draft["awaiting_edit"] = True
        await query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Yeni metni gönder, taslağı ona göre güncelleyeceğim.",
        )


def main():
    if not BOT_TOKEN or not CHANNEL_ID or not ADMIN_IDS:
        raise SystemExit(
            "BOT_TOKEN, CHANNEL_ID ve ADMIN_IDS ortam değişkenlerini .env dosyasında tanımla."
        )

    app: Application = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("Bot başlatıldı, mesajlar bekleniyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
