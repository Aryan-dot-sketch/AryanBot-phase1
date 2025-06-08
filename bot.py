import json
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import requests
import os

# ✅ Load values from environment variables
BOT_TOKEN = os.getenv("telegram_bot_token")
OPENROUTER_API_KEY = os.getenv("openrouter_api_key")
MODEL = os.getenv("model", "openai/gpt-3.5-turbo")
MEMORY_FILE = os.getenv("memory_file", "memory.json")
SYSTEM_PROMPT_FILE = os.getenv("system_prompt_file", "prompts/system_prompt.txt")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        return json.load(f).get("chat_history", [])

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump({"chat_history": memory[-10:]}, f)  # store last 10 exchanges

def load_system_prompt():
    if os.path.exists(SYSTEM_PROMPT_FILE):
        with open(SYSTEM_PROMPT_FILE, "r") as f:
            return f.read()
    return ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey Aryan! Your AI bot is now live 🚀")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    memory = load_memory()

    memory.append({"role": "user", "content": user_input})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": load_system_prompt()}] + memory[-10:]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    reply = response.json()["choices"][0]["message"]["content"]

    memory.append({"role": "assistant", "content": reply})
    save_memory(memory)

    await update.message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
