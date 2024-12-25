import asyncio
import json
import os
from venv import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
    CitaBotBuilder,
    CustomerProfile,
    DocType,
    OperationType,
    Province,
    Office,
)
from citabot.utils import open_json_file

TOKEN = os.getenv("CITA_CATCHER_BOT")
LVL_1_ROUTES, LVL_2_ROUTES = range(2)


keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton("Solicitar cita", callback_data="request_appointment"),
            InlineKeyboardButton("Mostrar datos", callback_data="reveal_data"),
            InlineKeyboardButton("Cancelar", callback_data="cancel"),
        ]
    ]
)

user_data = {}
tasks = {}


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
    await update.message.reply_text(
        "Este bot se destina a ayudar a los extranjeros a solicitar citas de asilo\n"
        + "en las oficinas de extranjeria de manera GRATIS, como lo tenga que ser.",
        reply_markup=keyboard,
    )

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

    customer = CustomerProfile(
        anticaptcha_api_key=os.environ.get(
            "CITA_BOT_ANTICAPTCHA_KEY"
        ),  # Anti-captcha API Key (auto_captcha=False to disable it)
        auto_captcha=False,  # Enable anti-captcha plugin (if False, you have to solve reCaptcha manually and press ENTER in the Terminal)
        auto_office=True,
        driver_path=settings.get(
            "driver_path",
            "/Users/pavelbeard/Documents/Projects/cita_catcher/src/drivers/geckodriver",
        ),
        save_artifacts=True,  # Record available offices / take available slots screenshot
        province=Province.ALICANTE,  # put your province here
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
        offices=[Office.BENIDORM, Office.ALICANTE_COMISARIA],  # put your offices here
        proxy=False,
    )

    if update.effective_user.id not in tasks:
        await update.effective_message.reply_text("Bot started.")
        task = asyncio.create_task(
            CitaBotBuilder(context=customer).start(update, cycles=200)
        )
        tasks.update({update.effective_user.id: task})

    else:
        new_task = asyncio.create_task(
            CitaBotBuilder(context=customer).start(update, cycles=200)
        )
        old_task = tasks.pop(update.effective_user.id)
        old_task.cancel()

        tasks.update({update.effective_user.id: new_task})

        await update.effective_message.reply_text("La búsqueda reiniciada")


async def reveal_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if update.effective_user.id in tasks:
        task: asyncio.Task = tasks.pop(update.effective_user.id)
        task.cancel()

        await update.effective_message.reply_text("Cancelado...")
    else:
        await update.effective_message.reply_text("No hay tarea pendiente")


# START BOT
def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LVL_1_ROUTES: [
                CallbackQueryHandler(
                    request_appointment, pattern=r"^request_appointment$"
                ),
                CallbackQueryHandler(reveal_data, pattern=r"^reveal_data$"),
                CallbackQueryHandler(cancel, pattern=r"^cancel$"),
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
