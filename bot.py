import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.exceptions import TelegramBadRequest
import os
from dotenv import load_dotenv
load_dotenv()
# Токен вашего бота
BOT_TOKEN = str(os.getenv("API"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class SearchStates(StatesGroup):
    waiting_for_query = State()


# Главный приветственный текст
START_TEXT = (
    "📖 *Азбука прав потребителей*\n\n"
    "Я помогу тебе:\n"
    "• Вернуть товар в магазин или ПВЗ\n"
    "• Написать претензию\n"
    "• Пожаловаться в Роспотребнадзор\n\n"
    "Выбери интересующий раздел ниже:"
)

INFO_TEXTS = {
    "pvz": (
        "📦 *ПРОБЛЕМЫ В ПВЗ:*\n\n"
        "👕 *Не дают примерить* — Вы имеете право осмотреть и примерить товар. Отказ незаконен.\n\n"
        "🚫 *Навязывают услуги* (страховка, упаковка) — Это запрещено ст. 16 ЗоЗПП.\n\n"
        "📦 *Потеряли заказ* — Ответственность на продавце. Требуйте деньги с него.\n\n"
        "💰 *Требуют доплату* — За хранение или проверку платить не нужно.\n\n"
        "🔍 *Не дают проверить товар* — Вы можете вскрыть упаковку и включить товар до оплаты.\n\n"
        "⛔️ *Отказали в выдаче* — Можете забрать по паспорту или данным из аккаунта."
    ),
    "return": (
        "✅ *ВОЗВРАТ ТОВАРА (ст. 25 ЗоЗПП)*\n\n"
        "• Вернуть можно в течение 14 дней\n"
        "• Товар не должен быть в употреблении\n"
        "• *НЕЛЬЗЯ вернуть:* продукты, лекарства, парфюмерию, технику с лицензией\n\n"
        "Без чека? Не проблема — можно ссылаться на свидетелей или выписку из банка."
    ),
    "warranty": (
        "🛠 *ГАРАНТИЯ И СРОКИ*\n\n"
        "• Срок гарантии: от 15 дней до 2 лет\n"
        "• Возврат денег за брак — до 10 дней\n"
        "• Ремонт по гарантии — до 45 дней\n"
        "• Замена товара — до 20 дней\n\n"
        "Если товар сломался в первые 15 дней — можете сразу требовать возврат или замену."
    ),
    "pretension": (
        "📄 *ШАБЛОН ПРЕТЕНЗИИ (скопируй и вставь)*\n\n"
        "`Кому: [Название магазина/ПВЗ]\n"
        "От: [Ваши ФИО], тел: [Телефон]\n"
        "Заказ № [номер] от [дата]\n\n"
        "При получении/покупке обнаружены недостатки:\n"
        "[опишите проблему]\n\n"
        "На основании ст. 18 ЗоЗПП требую:\n"
        "‣ Вернуть деньги\n"
        "‣ Заменить товар\n\n"
        "Дата: ______   Подпись: ______`\n\n"
        "❗️*Отправляй заказным письмом или через форму на сайте. Сохрани подтверждение!*"
    ),
    "rospotrebnadzor": (
        "🏛 *КАК ПОЖАЛОВАТЬСЯ В РОСПОТРЕБНАДЗОР*\n\n"
        "1. Напиши претензию продавцу (жди ответа 10 дней)\n"
        "2. Зайди на сайт: роспотребнадзор.рф → «Обращения граждан»\n"
        "3. Приложи: чек, претензию, ответ продавца\n"
        "4. Срок рассмотрения — 30 дней\n\n"
        "Бесплатно. Можно анонимно."
    )
}

SEARCH_KEYWORDS = {
    "пвз": "pvz", "примерка": "pvz", "доплата": "pvz", "проверка": "pvz", "выдача": "pvz",
    "возврат": "return", "чек": "return", "14 дней": "return", "купить": "return", "магазин": "return",
    "гарантия": "warranty", "ремонт": "warranty", "замена": "warranty", "сломался": "warranty", "брак": "warranty",
    "претензия": "pretension", "шаблон": "pretension", "заявление": "pretension", "исковое": "pretension",
    "роспотребнадзор": "rospotrebnadzor", "жалоба": "rospotrebnadzor"
}


# Генерация клавиатуры (добавлена кнопка возврата в главное меню)
def get_main_keyboard(show_back_button=False):
    buttons = [
        [InlineKeyboardButton(text="📦 Проблемы с ПВЗ", callback_data="btn_pvz")],
        [InlineKeyboardButton(text="✅ Возврат товара", callback_data="btn_return")],
        [InlineKeyboardButton(text="🛠 Гарантия и сроки", callback_data="btn_warranty")],
        [InlineKeyboardButton(text="📄 Шаблон претензии", callback_data="btn_pretension")],
        [InlineKeyboardButton(text="🏛 Роспотребнадзор", callback_data="btn_rospotrebnadzor")],
        [InlineKeyboardButton(text="🔍 Поиск по слову", callback_data="btn_search")]
    ]
    if show_back_button:
        buttons.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="btn_main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="pvz", description="Проблемы с ПВЗ"),
        BotCommand(command="return", description="Возврат товара"),
        BotCommand(command="warranty", description="Гарантия и сроки"),
        BotCommand(command="pretension", description="Шаблон претензии"),
        BotCommand(command="rospotrebnadzor", description="Жалоба в Роспотребнадзор"),
        BotCommand(command="search", description="Поиск по слову")
    ]
    await bot.set_my_commands(commands)


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(START_TEXT, reply_markup=get_main_keyboard(), parse_mode="Markdown")


# Обработка нажатий на инлайн-кнопки
@dp.callback_query(F.data.startswith("btn_"))
async def callback_handler(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]

    try:
        if action == "main":
            await state.clear()
            await callback.message.edit_text(
                text=START_TEXT,
                reply_markup=get_main_keyboard(show_back_button=False),
                parse_mode="Markdown"
            )
        elif action == "search":
            await state.set_state(SearchStates.waiting_for_query)
            await callback.message.edit_text(
                text="Введите ключевое слово для поиска (например: *брак*, *примерка*, *чек*, *жалоба*):",
                reply_markup=get_main_keyboard(show_back_button=True),
                parse_mode="Markdown"
            )
        elif action in INFO_TEXTS:
            await state.clear()
            await callback.message.edit_text(
                text=INFO_TEXTS[action],
                reply_markup=get_main_keyboard(show_back_button=True),
                parse_mode="Markdown"
            )
    except TelegramBadRequest:
        # Игнорируем ошибку, если текст сообщения не изменился при повторном нажатии
        pass

    await callback.answer()


# Текстовые команды (если пользователь вводит команды вручную)
@dp.message(Command("pvz"))
@dp.message(F.text.lower().in_({"pvz", "пвз"}))
async def cmd_pvz(message: types.Message):
    await message.answer(INFO_TEXTS["pvz"], reply_markup=get_main_keyboard(show_back_button=True),
                         parse_mode="Markdown")


@dp.message(Command("return"))
@dp.message(Command("vozvrat"))
@dp.message(F.text.lower().in_({"return", "vozvrat", "возврат"}))
async def cmd_return(message: types.Message):
    await message.answer(INFO_TEXTS["return"], reply_markup=get_main_keyboard(show_back_button=True),
                         parse_mode="Markdown")


@dp.message(Command("warranty"))
@dp.message(Command("garantiya"))
@dp.message(F.text.lower().in_({"warranty", "garantiya", "гарантия"}))
async def cmd_warranty(message: types.Message):
    await message.answer(INFO_TEXTS["warranty"], reply_markup=get_main_keyboard(show_back_button=True),
                         parse_mode="Markdown")


@dp.message(Command("pretension"))
@dp.message(Command("pretenziya"))
@dp.message(F.text.lower().in_({"pretension", "pretenziya", "претензия"}))
async def cmd_pretension(message: types.Message):
    await message.answer(INFO_TEXTS["pretension"], reply_markup=get_main_keyboard(show_back_button=True),
                         parse_mode="Markdown")


@dp.message(Command("rospotrebnadzor"))
@dp.message(F.text.lower() == "rospotrebnadzor")
async def cmd_rospotrebnadzor(message: types.Message):
    await message.answer(INFO_TEXTS["rospotrebnadzor"], reply_markup=get_main_keyboard(show_back_button=True),
                         parse_mode="Markdown")


@dp.message(Command("search"))
@dp.message(F.text.lower() == "search")
async def cmd_search(message: types.Message, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_query)
    await message.answer("Введите ключевое слово для поиска (например: *брак*, *примерка*, *чек*, *жалоба*):",
                         reply_markup=get_main_keyboard(show_back_button=True), parse_mode="Markdown")


# Обработчик текстового поиска
@dp.message(SearchStates.waiting_for_query)
async def process_search(message: types.Message, state: FSMContext):
    query = message.text.lower().strip()
    found_key = None

    for keyword, section in SEARCH_KEYWORDS.items():
        if keyword in query:
            found_key = section
            break

    if found_key:
        text = f"Результат по вашему запросу:\n\n{INFO_TEXTS[found_key]}"
    else:
        text = (
            "К сожалению, по этому слову ничего не найдено.\n"
            "Попробуйте ввести другие ключевые слова (например: *возврат*, *брак*, *пвз*, *гарантия*)."
        )

    # Отправляем результат поиска новым сообщением с прикрепленной клавиатурой
    await message.answer(text, reply_markup=get_main_keyboard(show_back_button=True), parse_mode="Markdown")
    await state.clear()


async def main():
    await set_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")