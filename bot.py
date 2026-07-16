import json
import os
import asyncio
import random
from telegram import Update, ReactionTypeEmoji
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

CONFIG_FILE = "tokens.json"
EMOJIS = ["🔥", "❤️", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🎉", "⚡", "😈", "💯", "👍", "🤩"]
reaction_lock = asyncio.Lock()

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None

def save_config(admin_id, tokens):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"admin_id": admin_id, "tokens": tokens}, f)

def setup():
    config = load_config()
    if not config:
        print("--- İLK KURULUM ---")
        admin_id = input("Admin ID girin: ")
        tokens = []
        while True:
            t = input(f"{len(tokens) + 1}. Bot Tokenını girin (Bitti ise 'devam' yazın): ").strip()
            if t.lower() == 'devam':
                if len(tokens) == 0:
                    print("En az 1 bot eklemelisiniz!")
                    continue
                break
            if t:
                tokens.append(t)
        save_config(admin_id, tokens)
        print(f"\n{len(tokens)} adet bot başarıyla kaydedildi!")
        return admin_id, tokens
    return config["admin_id"], config["tokens"]

async def queue_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return

    emoji = random.choice(EMOJIS)
    
    async with reaction_lock:
        try:
            await context.bot.set_message_reaction(
                chat_id=message.chat_id,
                message_id=message.message_id,
                reaction=[ReactionTypeEmoji(emoji=emoji)]
            )
            print(f"Bot ({context.bot.token[:8]}...) tepki koydu: {emoji}")
        except Exception as e:
            print(f"Hata: {e}")
        
        await asyncio.sleep(1)

async def start_bot(token):
    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), queue_reaction))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    return app

async def main():
    admin_id, tokens = setup()
    print(f"\n{len(tokens)} adet bot aktif ediliyor. Lütfen bekleyin...")
    
    # Tüm botları başlat
    tasks = [start_bot(token) for token in tokens]
    await asyncio.gather(*tasks)
    
    # Botlar başladıktan sonra programın kapanmaması için sonsuz bekleme
    print("Tüm botlar aktif! Kanala mesaj atarak test edebilirsin. Çıkmak için Ctrl+C.")
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSistem kapatıldı.")
