import os
import re
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Загружаем переменные окружения
load_dotenv()

# ============================================================
#  НАСТРОЙКИ БОТА
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Добавь его в Secrets.")

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


# ============================================================
#  БЕЗОПАСНЫЙ КАЛЬКУЛЯТОР
# ============================================================
def safe_calculate(expression: str):
    """
    Безопасно вычисляет математическое выражение.
    Поддерживает: + - * / ** // % ( ) и числа.
    """
    # Убираем пробелы
    expression = expression.replace(" ", "")
    
    # Заменяем символы для удобства
    expression = expression.replace("×", "*").replace("÷", "/")
    expression = expression.replace("^", "**")
    expression = expression.replace(",", ".")
    
    # Проверяем, что в выражении только разрешённые символы
    allowed = re.compile(r'^[0-9+\-*/().%\s]+$')
    if not allowed.match(expression):
        return None, "❌ Недопустимые символы в выражении!"
    
    # Запрещаем опасные конструкции
    if "__" in expression or "import" in expression or "eval" in expression:
        return None, "❌ Недопустимое выражение!"
    
    try:
        # Вычисляем с ограничениями
        result = eval(expression, {"__builtins__": {}}, {})
        
        # Округляем до 10 знаков после запятой
        if isinstance(result, float):
            result = round(result, 10)
            # Убираем .0 если целое
            if result.is_integer():
                result = int(result)
        
        return result, None
    except ZeroDivisionError:
        return None, "❌ Деление на ноль!"
    except SyntaxError:
        return None, "❌ Синтаксическая ошибка!"
    except Exception as e:
        return None, f"❌ Ошибка: {str(e)}"


# ============================================================
#  КОМАНДА /start
# ============================================================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Приветствие."""
    text = (
        "🧮 <b>Привет! Я бот-калькулятор!</b>\n\n"
        "Просто напиши мне математическое выражение — я посчитаю.\n\n"
        "📝 <b>Примеры:</b>\n"
        "• <code>2 + 2</code>\n"
        "• <code>10 * 5</code>\n"
        "• <code>100 / 4</code>\n"
        "• <code>2 ** 10</code> (степень)\n"
        "• <code>(5 + 3) * 2</code>\n"
        "• <code>15 % 4</code> (остаток)\n"
        "• <code>17 // 5</code> (целое деление)\n\n"
        "🔣 <b>Символы:</b>\n"
        "<code>+</code> — плюс\n"
        "<code>-</code> — минус\n"
        "<code>*</code> или <code>×</code> — умножить\n"
        "<code>/</code> или <code>÷</code> — разделить\n"
        "<code>**</code> или <code>^</code> — степень\n"
        "<code>%</code> — остаток\n"
        "<code>//</code> — целое деление\n\n"
        "🚀 <b>Просто пиши пример в чат!</b>"
    )
    await message.answer(text)


# ============================================================
#  КОМАНДА /help
# ============================================================
@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь."""
    text = (
        "📖 <b>Помощь</b>\n\n"
        "<b>Как пользоваться:</b>\n"
        "Просто напиши математическое выражение, и я его посчитаю.\n\n"
        "✅ <b>Работает:</b>\n"
        "• Сложение: <code>5 + 3</code>\n"
        "• Вычитание: <code>10 - 7</code>\n"
        "• Умножение: <code>4 * 6</code>\n"
        "• Деление: <code>20 / 5</code>\n"
        "• Степень: <code>2 ** 8</code>\n"
        "• Скобки: <code>(2 + 3) * 4</code>\n"
        "• Проценты: <code>200 * 15 / 100</code>\n\n"
        "❌ <b>Не работает:</b>\n"
        "• Буквы и текст\n"
        "• Другие математические функции\n\n"
        "🔄 <b>Команды:</b>\n"
        "/start — приветствие\n"
        "/help — эта справка\n"
        "/calc — пример\n"
    )
    await message.answer(text)


# ============================================================
#  КОМАНДА /calc
# ============================================================
@dp.message(Command("calc"))
async def cmd_calc(message: Message):
    """Пример вычисления."""
    text = (
        "🧮 <b>Пример работы:</b>\n\n"
        "Ты пишешь: <code>(5 + 3) * 2</code>\n"
        "Я отвечаю: <b>16</b>\n\n"
        "Попробуй сам! 👇"
    )
    await message.answer(text)


# ============================================================
#  ОСНОВНАЯ ЛОГИКА — ВЫЧИСЛЕНИЕ ВЫРАЖЕНИЙ
# ============================================================
@dp.message()
async def calculate_handler(message: Message):
    """Обрабатывает любое сообщение как математическое выражение."""
    text = message.text.strip()
    
    if not text:
        await message.answer("⚠️ Пустое сообщение!")
        return
    
    # Пытаемся вычислить
    result, error = safe_calculate(text)
    
    if error:
        await message.answer(error)
        return
    
    # Форматируем ответ
    # Убираем лишние символы из исходного выражения для красоты
    display_expr = text.replace(" ", "")
    
    answer = (
        f"🧮 <b>Пример:</b> <code>{display_expr}</code>\n"
        f"📊 <b>Ответ:</b> <code>{result}</code>"
    )
    
    await message.answer(answer)


# ============================================================
#  ЗАПУСК
# ============================================================
async def main():
    logger.info("🧮 Бот-калькулятор запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Бот остановлен")
