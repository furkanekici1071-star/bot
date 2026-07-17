import json, os, asyncio, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReactionTypeEmoji
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

CONFIG_FILE = "config.json"
EMOJIS = ["🔥", "❤️", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🎉", "⚡", "😈", "💯"]

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    return {"admin_id": None, "master_token": None, "tokens": []}

def save_config(config):
    with open(CONFIG_FILE, "w") as f: json.dump(config, f)

# --- PANEL FONKSİYONLARI ---
async def admin_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    return str(update.effective_user.id) == str(config["admin_id"])

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    config = load_config()
    text = f"🛡 **Admin Paneli**\n\n🔹 Aktif Bot Sayısı: {len(config['tokens'])}\n\nKomutlar:\n/ekle <token> - Yeni bot ekle\n/liste - Kanalları göster"
    await update.message.reply_text(text, parse_mode="Markdown")

async def add_bot_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await admin_check(update, context): return
    if not context.args: return
    config = load_config()
    config["tokens"].append(context.args[0])
    save_config(config)
    await update.message.reply_text("✅ Yeni bot başarıyla havuza eklendi!")

# --- MASTER İŞLEMLERİ (Onay ve Reaksiyon) ---
async def request_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    if update.effective_chat.type == 'private': return # Sadece kanal/gruptan gelen mesajlara bak
    
    chat_name = update.effective_chat.title
    msg_id = update.effective_message.id
    
    keyboard = [[InlineKeyboardButton("✅ Onayla", callback_data=f"app_{update.effective_chat.id}_{msg_id}")]]
    await context.bot.send_message(
        chat_id=config["admin_id"],
        text=f"📢 {chat_name} kanalında mesaj var. Reaksiyon atılsın mı?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await admin_check(update, context): return
    
    _, chat_id, msg_id = query.data.split("_")
    await query.answer("Botlar tetikleniyor...")
    config = load_config()
    
    for token in config["tokens"]:
        try:
            bot = ApplicationBuilder().token(token).build().bot
            await bot.set_message_reaction(chat_id=chat_id, message_id=msg_id, reaction=[ReactionTypeEmoji(emoji=random.choice(EMOJIS))])
            await asyncio.sleep(0.5)
        except: continue
    await query.edit_message_text("✅ İşlem tamamlandı.")

# --- BAŞLATICILAR ---
async def main():
    config = load_config()
    if not config["admin_id"]:
        config["admin_id"] = input("Admin ID gir: ")
        config["master_token"] = input("Master Bot Token gir: ")
        save_config(config)

    master = ApplicationBuilder().token(config["master_token"]).build()
    master.add_handler(CommandHandler("panel", admin_panel))
    master.add_handler(CommandHandler("ekle", add_bot_cmd))
    master.add_handler(CallbackQueryHandler(handle_callback))
    # Mesajları dinle ve onaya gönder
    master.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, request_approval))
    
    print("Master Bot Aktif. İşlem için hazırım...")
    await master.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
