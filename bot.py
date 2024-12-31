import asyncio
import json
import os
from venv import logger
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from citabot import (
    CitaBot,
    CustomerProfile,
    DocType,
    OperationType,
    Province,
)
from citabot.utils import open_json_file

TOKEN = os.getenv("CITA_CATCHER_BOT")

LVL_1_ROUTES, LVL_2_ROUTES = range(2)


keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton("Solicitar cita", callback_data="province_select"),
            InlineKeyboardButton("Mostrar datos", callback_data="reveal_data"),
            InlineKeyboardButton("Cancelar", callback_data="cancel"),
            InlineKeyboardButton("Mostrar tareas", callback_data="show_tasks"),
        ]
    ]
)

province_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton("Alicante", callback_data=Province.ALICANTE.name),
            InlineKeyboardButton("Murcia", callback_data=Province.MURCIA.name),
        ]
    ]
)

cancel_province_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                "Alicante", callback_data=Province.ALICANTE.name + "_cancel"
            ),
            InlineKeyboardButton(
                "Murcia", callback_data=Province.MURCIA.name + "_cancel"
            ),
        ]
    ]
)

user_data = {}


def find(iterable, predicate):
    return next((x for x in iterable if predicate(x)), None)


# HANDLERS
async def data_json_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    document = update.message.document
    user_id = update.effective_user.id

    if document:
        file_id = document.file_id
        new_file = await context.bot.get_file(file_id)
        file_data = await new_file.download_as_bytearray()

        user_data.update({user_id: json.loads(file_data.decode("utf-8"))})

    await update.message.reply_text("Datos han sido recibidos")
    await update.message.reply_text("Elige una opción:", reply_markup=keyboard)


# COMMANDS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Welcome message"""
    await update.effective_message.reply_text(
        "Este bot se destina a ayudar a los extranjeros a solicitar citas de asilo\n"
        + "en las oficinas de extranjeria de manera GRATIS, como lo tenga que ser.",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["Iniciar la búsqueda", "Mostrar tareas"],
            ],
            one_time_keyboard=True,
        ),
    )

    return LVL_1_ROUTES


async def province_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    await update.effective_message.reply_text(
        "Seleccione la provincia de la que quieres solicitar citas",
        reply_markup=province_keyboard,
    )

    return LVL_2_ROUTES


async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    provinces = [p.name for p in [Province.ALICANTE, Province.MURCIA]]
    tasks = []
    for province in provinces:
        task = find(asyncio.tasks.all_tasks(), lambda task: task.get_name() == province)
        if task:
            tasks.append(task.get_name())

    if len(tasks) == 0:
        await update.effective_message.reply_text("📋 No hay tareas pendientes")
        return LVL_1_ROUTES

    await update.effective_message.reply_text(f"📋 Tasks: {' | '.join(tasks)}")
    return LVL_1_ROUTES


async def request_appointment(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()

    data = open_json_file("data.json")
    user_data.update({query.from_user.id: data})

    settings = open_json_file("settings.json")

    logger.info("[settings.json] loaded. settings: %s", settings)

    if not data.get("doc_value"):
        await update.effective_message.reply_text("no hay datos de documento.")
        return

    if not data.get("country"):
        await update.effective_message.reply_text("no hay datos de pais.")
        return

    if not data.get("name"):
        await update.effective_message.reply_text("no hay datos de nombre.")
        return

    if not data.get("phone"):
        await update.effective_message.reply_text("no hay datos de telefono.")
        return

    if not data.get("email"):
        await update.effective_message.reply_text("no hay datos de email.")
        return

    if not data.get("year_of_birth"):
        await update.effective_message.reply_text(
            "no hay datos de fecha de nacimiento."
        )
        return

    province = find(
        Province,
        lambda province: province.name == update.callback_query.data,
    )

    customer = CustomerProfile(
        anticaptcha_api_key=os.environ.get(
            "CITA_BOT_ANTICAPTCHA_KEY"
        ),  # Anti-captcha API Key (auto_captcha=False to disable it)
        auto_captcha=False,  # Enable anti-captcha plugin (if False, you have to solve reCaptcha manually and press ENTER in the Terminal)
        auto_office=True,
        driver_path=settings.get(
            "driver_path",
            "/Users/pavelbeard/Documents/drivers/chromedriver",
        ),
        save_artifacts=True,  # Record available offices / take available slots screenshot
        province=province,  # put your province here
        operation_code=OperationType.RENOVACION_ASILO,
        doc_type=DocType.NIE,  # DocType.NIE or DocType.PASSPORT
        doc_value=data["doc_value"],  # NIE or Passport number, no spaces.
        country=data["country"],
        name=data["name"],  # Your Name
        phone=data["phone"],  # Phone number (use this format, please)
        email=data["email"],  # Email
        year_of_birth=data["year_of_birth"],
        min_date="30/01/2025",
        max_date="25/02/2025",
        min_time="9:00",
        max_time="18:00",
        sms_webhook_token=os.getenv("CITA_BOT_WEBHOOK_TOKEN"),
        reason_or_type="Renovar la documentación por caducación",
        # Offices in order of preference
        # This selects specified offices one by one or a random one if not found.
        # For recogida only the first specified office will be attempted or none
        # offices=[Office.BENIDORM, Office.ALICANTE_COMISARIA],  # put your offices here
        proxy=False,
    )

    province_task = find(
        asyncio.tasks.all_tasks(), lambda task: task.get_name() == province.name
    )
    if not province_task:
        await update.effective_message.reply_text(
            "Bot comenzando en la provincia de {}".format(province.name)
        )
        task_builder = CitaBot(context=customer, update=update)
        asyncio.create_task(task_builder.start(cycles=200), name=province.name)
    else:
        await update.effective_message.reply_text("La provincia ya está en ejecución")

    return LVL_2_ROUTES


async def reveal_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    username = update.effective_user.username
    if user_id not in user_data:
        await update.effective_message.reply_text("No hay datos para mostrar")
    else:
        await update.effective_message.reply_markdown(
            f"**Datos de usuario: {username or user_id}**\n"
            f"`doc_value`: {user_data[user_id]['doc_value']}\n"
            f"`country`: {user_data[user_id]['country']}\n"
            f"`name`: {user_data[user_id]['name']}\n"
            f'`phone`: {user_data[user_id]["phone"]}\n'
            f"`email`: {user_data[user_id]['email']}\n"
            f'`year_of_birth`: {user_data[user_id]["year_of_birth"]}\n'
        )

    return ConversationHandler.END


async def cancel_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await update.effective_message.reply_text(
        "Elige la provincia de la que quieres cancelar:",
        reply_markup=cancel_province_keyboard,
    )

    return LVL_2_ROUTES


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    province = find(
        Province,
        lambda province: province.name == update.callback_query.data.split("_")[0],
    )

    province_task = find(
        asyncio.tasks.all_tasks(), lambda task: task.get_name() == province.name
    )

    if province_task:
        province_task.cancel()
        await update.effective_message.reply_text(f"Cancelado: {province.name}")

    else:
        await update.effective_message.reply_text(
            f"No hay tarea pendiente para {province.name}"
        )

    return ConversationHandler.END


async def reply_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text
    query = update.callback_query

    if query:
        await query.answer()

    if message == "Iniciar la búsqueda":
        reply_message = "Elige la provincia de la que quieres solicitar citas:"
        kb = province_keyboard

    elif message == "Mostrar tareas":
        tasks = list(
            map(
                lambda x: x.get_name(),
                [
                    t
                    for t in asyncio.tasks.all_tasks()
                    if t.get_name() in [Province.ALICANTE.name, Province.MURCIA.name]
                ],
            )
        )

        if len(tasks) == 0:
            reply_message = "No hay tareas"
            kb = None
        else:
            reply_message = "Si quiere cancelar la búsqueda, elige la provincia de la que quieres cancelar:"

            inline_keyboard = [[]]
            for task in tasks:
                inline_keyboard[0].append(
                    InlineKeyboardButton(task, callback_data=f"{task}_cancel")
                )

            kb = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await update.message.reply_text(
        text=reply_message,
        reply_markup=kb,
    )

    return LVL_1_ROUTES


async def callback_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    cb_data = update.callback_query.data

    provinces = [p.name for p in [Province.ALICANTE, Province.MURCIA]]

    if cb_data in [p for p in provinces]:
        await request_appointment(update, context)
    elif cb_data in [p + "_cancel" for p in provinces]:
        await cancel(update, context)
    elif cb_data == "reveal_data":
        await reveal_data(update, context)

    return LVL_1_ROUTES


# START BOT
def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LVL_1_ROUTES: [
                CallbackQueryHandler(callback_menu, pattern=r"^\w+$"),
                MessageHandler(
                    filters=filters.TEXT & ~filters.COMMAND, callback=reply_menu
                ),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(
        MessageHandler(filters=filters.ATTACHMENT, callback=data_json_handler)
    )
    app.run_polling()


if __name__ == "__main__":
    if not TOKEN:
        print("Please set CITA_CATCHER_BOT env variable")
        exit(1)

    main()
