import os
import json
from venv import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from mimetypes import guess_extension
from document_processor import DocumentProcessor
from image_processor import ImageProcessor
from video_processor import VideoProcessor


# Bot Token
BOT_TOKEN = '7881068420:AAG6t17WXbf9kKqAZkICxVndz4MXIRRgbpg'
UPLOAD_DIR = 'uploads'

# Initialize processors
document_processor = DocumentProcessor(output_dir=UPLOAD_DIR)
image_processor = ImageProcessor(output_dir=UPLOAD_DIR)
video_processor = VideoProcessor()

# Ensure upload directory exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data.clear()

    # Create inline keyboard
    keyboard = [
        [InlineKeyboardButton("تصویر", callback_data="media_image")],
        [InlineKeyboardButton("ویدئو", callback_data="media_video")],
        [InlineKeyboardButton("سند", callback_data="media_document")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "سلام! لطفاً نوع رسانه‌ای که قصد استفاده از آن را دارید انتخاب کنید:",
        reply_markup=reply_markup
    )

async def handle_media_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['media_type'] = query.data.split('_')[1]
    context.user_data['waiting_for_upload'] = True

    keyboard = [[InlineKeyboardButton("بازگشت", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    media_name = {"image": "تصویر", "video": "ویدئو", "document": "سند"}[context.user_data['media_type']]
    await query.edit_message_text(f"لطفاً {media_name} خود را بارگذاری کنید:", reply_markup=reply_markup)

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    media_type = context.user_data.get('media_type')
    if not media_type:
        await update.message.reply_text("لطفاً ابتدا نوع رسانه را انتخاب کنید.")
        return

    if not context.user_data.get('waiting_for_upload', False):
        await update.message.reply_text("لطفاً تنها نوع رسانه‌ی انتخاب‌شده را بارگذاری کنید.")
        return

    file = update.message.document
    if not file:
        await update.message.reply_text("لطفاً یک فایل ارسال کنید.")
        return

    file_obj = await file.get_file()
    file_path = os.path.join(UPLOAD_DIR, f"{update.effective_user.id}_{file.file_name}")
    await file_obj.download_to_drive(file_path)

    context.user_data['file_path'] = file_path
    context.user_data['waiting_for_upload'] = False

    if media_type == 'image':
        keyboard = [
            [InlineKeyboardButton("چرخش تصویر", callback_data="process_rotate")],
            [InlineKeyboardButton("حذف پس‌زمینه", callback_data="process_removebg")],
            [InlineKeyboardButton("اضافه کردن زیرنویس", callback_data="process_addcaption")],
            [InlineKeyboardButton("کراپ", callback_data="process_crop")],
            [InlineKeyboardButton("نغییر فرمت", callback_data="process_format")],
            [InlineKeyboardButton("بازگشت", callback_data="back")]
        ]
    elif media_type == 'video':
        keyboard = [
            [InlineKeyboardButton("تغییر رزولوشن", callback_data="process_resolution")],
            [InlineKeyboardButton("تغییر نرخ فریم", callback_data="process_framerate")],
            [InlineKeyboardButton("ادغام ویدئوها", callback_data="process_merge")],
            [InlineKeyboardButton("برش ویدئو", callback_data="process_trim")],
            [InlineKeyboardButton("استخراج صوت", callback_data="process_extract_audio")],
            [InlineKeyboardButton("اضافه کردن زیرنویس", callback_data="process_add_caption")],
            [InlineKeyboardButton("بازگشت", callback_data="back")]
        ]
    elif media_type == 'document':
        keyboard = [
            [InlineKeyboardButton("ادغام فایل‌های PDF", callback_data="process_merge")],
            [InlineKeyboardButton("تقسیم PDF", callback_data="process_split")],
            [InlineKeyboardButton("فشرده‌سازی PDF", callback_data="process_compress")],
            [InlineKeyboardButton("OCR (تشخیص متن)", callback_data="process_ocr")],
            [InlineKeyboardButton("بازگشت", callback_data="back")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفاً نوع عملیات را انتخاب کنید:", reply_markup=reply_markup)

async def handle_processing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    process_type = query.data.split('_')[1]
    file_path = context.user_data.get('file_path')

    if not file_path:
        await query.edit_message_text("خطایی رخ داده است. لطفاً /start را وارد کنید.")
        return

    if process_type == "merge":
        await query.edit_message_text("لطفاً فایل‌های دیگری که می‌خواهید ادغام کنید ارسال نمایید.")
        context.user_data['waiting_for_merge'] = "merge"

    elif process_type == "split":
        await query.edit_message_text("لطفاً محدوده صفحات را به فرمت start-end وارد کنید. مثال: 1-3")
        context.user_data['waiting_for_input'] = "split"

    elif process_type == "compress":
        await query.edit_message_text("لطفاً کیفیت فشرده‌سازی را انتخاب کنید: low, medium، یا high.")
        context.user_data['waiting_for_input'] = "compress"

    elif process_type == "ocr":
        await query.edit_message_text("لطفاً فرمت خروجی OCR را مشخص کنید: pdf, docx، یا md.")
        context.user_data['waiting_for_input'] = "ocr"

    elif process_type == "rotate":
        await query.edit_message_text("لطفاً زاویه چرخش را وارد کنید (مثال: 90):")
        context.user_data['waiting_for_input'] = "rotate"

    elif process_type == "crop":
        await query.edit_message_text("لطفا وارد کنید از هر طرف چند درصد از تصویر کات شود برای مثال 10-10-10-10")
        context.user_data['waiting_for_input'] = "crop"

    elif process_type == "format":
        await query.edit_message_text("فرمت جدید را وارد کنید ")
        context.user_data['waiting_for_input'] = "format"

    elif process_type == "removebg":
        output_path = image_processor.remove_background(file_path)
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))

    elif process_type == "addcaption":
        await query.edit_message_text("لطفاً متن زیرنویس را وارد کنید:")
        context.user_data['waiting_for_input'] = "addcaption"

    elif process_type == "resolution":
        await query.edit_message_text("لطفاً رزولوشن جدید (عرضxارتفاع) را وارد کنید. مثال: 1280x720")
        context.user_data['waiting_for_input'] = "resolution"

    elif process_type == "framerate":
        await query.edit_message_text("لطفاً نرخ فریم جدید را وارد کنید. مثال: 30")
        context.user_data['waiting_for_input'] = "framerate"

    elif process_type == "trim":
        await query.edit_message_text("لطفاً بازه زمانی برای برش را وارد کنید (مثال: 00:00:10-00:00:30)")
        context.user_data['waiting_for_input'] = "trim"

    elif process_type == "add_caption":
        await query.edit_message_text("لطفاً متن زیرنویس و زمان شروع و پایان را وارد کنید (مثال: متن, 5, 10)")
        context.user_data['waiting_for_input'] = "add_caption"

async def handle_additional_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting_for = context.user_data.get('waiting_for_input')
    file_path = context.user_data.get('file_path')

    if waiting_for == "split":
        try:
            ranges = update.message.text.split('-')
            intervals = [(int(ranges[0]), int(ranges[1]))]
            output_paths = document_processor.split_pdf(file_path, intervals, output_prefix=None)
            for output_path in output_paths:
                await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))
        except Exception as e:
            await update.message.reply_text(f"خطا: {e}")

    elif waiting_for == "compress":
        try:
            quality = update.message.text.lower()
            output_path = document_processor.compress_pdf(file_path, quality=quality)
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))
        except Exception as e:
            await update.message.reply_text(f"خطا: {e}")

    elif waiting_for == "merge":
        try:
            # quality = update.message.text.lower()
            # output_filename = 
            output_path = document_processor.compress_pdf(file_path, output_filename=None)
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))
        except Exception as e:
            await update.message.reply_text(f"خطا: {e}")
    

    elif waiting_for == "ocr":
        try:
            format = update.message.text.lower()
            output_path = document_processor.ocr_document(file_path, output_format=format)
            await update.message.reply_document(open(output_path, 'rb'))
        except Exception as e:
            await update.message.reply_text(f"خطا: {e}")

    elif waiting_for == "rotate":
        try:
            angle = int(update.message.text)
            output_path = image_processor.rotate_image(file_path, angle)
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))
        except ValueError:
            await update.message.reply_text("لطفاً یک عدد صحیح وارد کنید.")
    elif waiting_for == "crop":
            try:
                t, b,r,l = map(int, update.message.text.split('-'))
                output_path = image_processor.crop_image(file_path, crop_top=t,crop_bottom=b,crop_left=r,crop_right=l)
                await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))
            except ValueError:
                await update.message.reply_text("لطفاً یک عدد صحیح وارد کنید.")
    elif waiting_for == "format":
            try:
                format=update.message.text
                output_path = image_processor.change_format(file_path, new_format=format)
                await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))
            except ValueError:
                await update.message.reply_text("لطفاً فرمت صحیح را وارد کنید")
    elif waiting_for == "addcaption":
        caption_text = update.message.text
         # Define a small region to see the box expansion
        box_vertices = [(0.4, 0.4), (0.5, 0.4), (0.5, 0.45), (0.4, 0.45)]
        
        output_path = image_processor.add_caption(file_path, caption_text,
        box_vertices=box_vertices,
        box_color=(0, 0, 0, 128),
        padding=10,
        font_name="Consolas",
        font_size=20,
        font_color=(255, 255, 255, 255),
        output_path=None,
        text_position="center")
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))

    elif waiting_for == "resolution":
        try:
            width, height = map(int, update.message.text.split('x'))
            output_path = os.path.splitext(file_path)[0] + f"_{width}x{height}.mp4"
            video_processor.change_resolution(file_path, output_path, (width, height))
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))
        except Exception as e:
            await update.message.reply_text(f"خطا: {e}")

    elif waiting_for == "framerate":
        try:
            framerate = int(update.message.text)
            output_path = os.path.splitext(file_path)[0] + f"_{framerate}fps.mp4"
            video_processor.change_framerate(file_path, output_path, framerate)
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))
        except Exception as e:
            await update.message.reply_text(f"خطا: {e}")

    elif waiting_for == "trim":
        try:
            start, end = update.message.text.split('-')
            intervals = [(start, end)]
            output_paths = video_processor.trim_video(file_path, intervals, UPLOAD_DIR)
            for output_path in output_paths:
                await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))
        except Exception as e:
            await update.message.reply_text(f"خطا: {e}")

    elif waiting_for == "add_caption":
        try:
            text, start_time, end_time = update.message.text.split(',')
            output_path = os.path.splitext(file_path)[0] + "_captioned.mp4"
            video_processor.add_caption(file_path, output_path, text, float(start_time), float(end_time))
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))
        except Exception as e:
            await update.message.reply_text(f"خطا: {e}")
    

    context.user_data['waiting_for_input'] = None





async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("تصویر", callback_data="media_image")],
        [InlineKeyboardButton("ویدئو", callback_data="media_video")],
        [InlineKeyboardButton("سند", callback_data="media_document")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "سلام! لطفاً نوع رسانه‌ای که قصد استفاده از آن را دارید انتخاب کنید:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Welcome to the bot! Here are the available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "You can also interact with the bot using the buttons provided."
    )
    await update.message.reply_text(help_text)

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Button clicked!")

# # Main function
# def main():
#     # Replace with your actual Telegram bot token
#     TOKEN = '7800194193:AAHThD3FWW6CwC2KBXVjRzM_LvyP5eTmwJ4'

#     # Create the Application
#     application = Application.builder().token(TOKEN).build()

#     # Add handlers for commands and interactions
#     application.add_handler(CommandHandler("start", start))
#     # application.add_handler(CallbackQueryHandler(button_callback))
#     application.add_handler(MessageHandler(filters.Document.ALL, handle_file_upload))
#     application.add_handler(CommandHandler("help", help_command))

#     # Set bot commands for better user experience
#     commands = [
#         BotCommand("start", "Start the bot"),
#         BotCommand("help", "Get help using the bot"),
#     ]
#     application.bot.set_my_commands(commands)

#     # Run the bot
#     print("Bot is running. Press Ctrl+C to stop.")
#     application.run_polling()


# ***********************************************************************
def main():
    # Initialize Application with token
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers for basic commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Callback and message handlers
    application.add_handler(CallbackQueryHandler(handle_media_selection, pattern="^media_"))
    application.add_handler(CallbackQueryHandler(handle_processing, pattern="^process_"))
    application.add_handler(CallbackQueryHandler(handle_back, pattern="^back$"))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file_upload))
    application.add_handler(MessageHandler(filters.TEXT, handle_additional_input))

    # Set bot commands for user convenience
    commands = [
        BotCommand("start", "Start interacting with the bot"),
        BotCommand("help", "Get detailed instructions"),
    ]
    application.bot.set_my_commands(commands)

    # Start the bot
    logger.info("Bot is running...")
    application.run_polling()
# ***********************************************************************
if __name__ == '__main__':
    main()

