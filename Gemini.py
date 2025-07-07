import os
import logging
from dotenv import load_dotenv

# Правильные импорты для python-telegram-bot v20.0+
from telegram import Update, Application
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Загружаем переменные окружения из файла .env
load_dotenv()

# ... (остальной код остается тем же)

# --- Конфигурация ---
# Получаем токен Telegram бота из переменной окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") 
# Получаем API ключ Gemini из переменной окружения
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

# Проверяем, что токены и ключи установлены
if not TELEGRAM_BOT_TOKEN:
    logging.error("Переменная окружения TELEGRAM_BOT_TOKEN не установлена. Пожалуйста, добавьте её в файл .env")
    exit(1)
if not GEMINI_API_KEY:
    logging.error("Переменная окружения GEMINI_API_KEY не установлена. Пожалуйста, добавьте её в файл .env")
    exit(1)

# Настройка логирования для отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Используем модель gemini-pro для текстовых взаимодействий
    # Вы также можете попробовать другие модели, если они доступны и подходят для вашей задачи
    gemini_model = genai.GenerativeModel('gemini-pro') 
except Exception as e:
    logger.error(f"Ошибка при настройке Gemini API: {e}. Проверьте ваш GEMINI_API_KEY.")
    exit(1)

# --- Обработчики команд и сообщений ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start. Отправляет приветственное сообщение."""
    user = update.effective_user
    logger.info(f"Получена команда /start от пользователя {user.full_name} (ID: {user.id})")
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! Я бот на базе Gemini AI. Задай мне любой вопрос, и я постараюсь на него ответить.",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help. Отправляет сообщение с инструкциями."""
    logger.info(f"Получена команда /help от пользователя {update.effective_user.full_name}")
    await update.message.reply_text(
        "Я могу отвечать на твои вопросы, используя возможности Gemini AI.\n"
        "Просто отправь мне текстовое сообщение, и я постараюсь тебе помочь."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает текстовые сообщения от пользователя,
    отправляет их в Gemini API и возвращает ответ.
    """
    user_message = update.message.text
    user = update.effective_user
    logger.info(f"Получено сообщение от {user.full_name} (ID: {user.id}): {user_message}")

    # Уведомляем пользователя, что запрос обрабатывается
    await update.message.reply_text("Думаю над ответом...")

    try:
        # Отправляем сообщение пользователя в Gemini API
        response = gemini_model.generate_content(user_message)
        gemini_response = response.text
        logger.info(f"Получен ответ от Gemini: {gemini_response[:100]}...") # Логируем часть ответа
        
        # Отправляем ответ от Gemini обратно пользователю
        await update.message.reply_text(gemini_response)
    except Exception as e:
        logger.error(f"Ошибка при обращении к Gemini API для сообщения '{user_message[:50]}...': {e}")
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке вашего запроса с помощью Gemini AI. "
            "Возможно, запрос был слишком сложным, или возникла проблема с сервисом."
            "\nПожалуйста, попробуйте переформулировать запрос или повторить попытку позже."
        )

# --- Основная функция запуска бота ---
def main() -> None:
    """Запускает бота."""
    logger.info("Инициализация Telegram бота...")
    # Создаем объект Application и передаем ему токен вашего бота
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Добавляем обработчик для всех текстовых сообщений, которые не являются командами
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен. Ожидание сообщений...")
    # Запускаем бота в режиме постоянного опроса (polling)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()