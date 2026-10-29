import logging
import os
from datetime import datetime

from telegram import Update, ForceReply
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

USER_LOG_FILE = 'user_logs.txt'


def log_user_data(user_id: int, username: str, first_name: str, last_name: str):
    """Логирует данные пользователя в файл."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user_info = (
        f"ID: {user_id}, Username: @{username if username else 'N/A'}, "
        f"Nickname: {first_name} {last_name if last_name else ''}, "
        f"Data Registration: {timestamp}\n"
    )
    with open(USER_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(user_info)
    logger.info(f"User data logged: {user_info.strip()}")


def get_user_stats():
    """Считывает статистику пользователей из файла логов."""
    total_users = 0
    unique_users = set()

    if not os.path.exists(USER_LOG_FILE):
        return 0, 0

    with open(USER_LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            total_users += 1
            try:
                user_id_str = line.split("ID: ")[1].split(",")[0].strip()
                unique_users.add(user_id_str)
            except IndexError:
                continue

    return total_users, len(unique_users)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start."""
    user = update.effective_user
    log_user_data(user.id, user.username, user.first_name, user.last_name)

    welcome_message = (
        f"Привет, {user.mention_html()}! Добро пожаловать.\n\n"
          "У нас есть эксклюзивные паки с темами: альтушки, дошколята, подростки и многое другое. "
        "Чтобы получить доступ, тебе нужно выполнить простое задание.\n\n"
        "**Задание:**\n"
        "1. Найди популярные видео в TikTok или других платформах.\n"
        "2. Оставь под ними комментарий, упомянув нашего бота (например, `@название_твоего_бота`).\n"
        "3. Чем больше комментариев и переходов по ссылке, тем быстрее ты получишь доступ к новым пакам!\n\n"
        "Мы отслеживаем трафик. Как только ты выполнишь задание, паки станут доступны."
    )

    await update.message.reply_html(
        welcome_message,
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /help."""
    await update.message.reply_text(
        "Просто следуй инструкциям в /start, чтобы получить доступ к контенту."
    )


async def ad_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Скрытая админ-панель для просмотра статистики."""
    admin_id = os.environ.get('ADMIN_ID')
    if not admin_id or str(update.effective_user.id) != admin_id:
        logger.warning(
            f"Unauthorized access attempt to /ad by user ID: {update.effective_user.id}"
        )
        await update.message.reply_text("Доступ запрещен.")
        return

    total_logs, unique_users = get_user_stats()
    stats_message = (
        "Статистика пользователей:\n"
        f"Всего записей в логе: {total_logs}\n"
        f"Уникальных пользователей: {unique_users}\n\n"
        f"Содержимое файла '{USER_LOG_FILE}':\n"
    )

    log_content = ""
    if os.path.exists(USER_LOG_FILE):
        with open(USER_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            log_content = "".join(lines[-20:])
            if len(lines) > 20:
                log_content = "...\n" + log_content

    await update.message.reply_text(stats_message + log_content)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отвечает на любое текстовое сообщение."""
    await update.message.reply_text(
        "Отлично! Продолжай привлекать трафик. Мы скоро проверим."
    )


def main() -> None:
    """Запускает бота."""
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set.")
        raise ValueError("BOT_TOKEN environment variable not set.")

    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ad", ad_panel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
