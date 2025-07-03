import os
import json
import logging
import subprocess
import ffmpeg
from pyrogram import Client, filters
from pyrogram.types import Message, Document, Audio

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
# Replace with your actual API ID, API Hash, and Bot Token
API_ID = os.environ.get("API_ID", 12345) # Placeholder
API_HASH = os.environ.get("API_HASH", "your_api_hash") # Placeholder
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token") # Placeholder

# Admin User IDs (replace with actual admin IDs or manage more dynamically)
ADMIN_USER_IDS = [123456789] # Placeholder

# Directories
USER_DATA_DIR = "user_data"
CONFIG_TEMPLATE_PATH = "config_template.json"

if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

# --- Pyrogram Client ---
app = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# --- Helper Functions ---
def get_user_config_path(user_id: int) -> str:
    """Gets the path to the user's config file."""
    return os.path.join(USER_DATA_DIR, str(user_id), "config.json")

def get_user_data_dir(user_id: int) -> str:
    """Gets the path to the user's data directory."""
    return os.path.join(USER_DATA_DIR, str(user_id))

def ensure_user_setup(user_id: int):
    """Ensures user directory and config file exist."""
    user_dir = get_user_data_dir(user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
        logger.info(f"Created directory for user {user_id}: {user_dir}")

    user_config_path = get_user_config_path(user_id)
    if not os.path.exists(user_config_path):
        try:
            with open(CONFIG_TEMPLATE_PATH, 'r') as template_f, open(user_config_path, 'w') as user_f:
                config_data = json.load(template_f)
                config_data["user_id"] = user_id # Set the user_id in their config
                json.dump(config_data, user_f, indent=2)
            logger.info(f"Copied config template to {user_config_path} for user {user_id}")
        except FileNotFoundError:
            logger.error(f"Config template {CONFIG_TEMPLATE_PATH} not found!")
        except Exception as e:
            logger.error(f"Error creating config for user {user_id}: {e}")


# --- Command Handlers ---
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handles the /start command."""
    user_id = message.from_user.id
    ensure_user_setup(user_id)
    logger.info(f"/start command from user {user_id}")
    await message.reply_text(
        "سلام! 👋 به ربات پردازشگر موزیک خوش آمدید.\n"
        "من می‌توانم به شما در ویرایش تگ‌ها، تبدیل فرمت، افزودن واترمارک و موارد دیگر کمک کنم.\n\n"
        "برای شروع، می‌توانید فایل موزیک خود را ارسال کنید.\n"
        "برای مشاهده لیست دستورات از /help استفاده کنید."
    )

@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Handles the /help command."""
    user_id = message.from_user.id
    logger.info(f"/help command from user {user_id}")
    help_text = (
        "راهنمای ربات پردازشگر موزیک:\n\n"
        "📖 **دستورات اصلی:**\n"
        "🔸 `/start` - شروع کار با ربات و ایجاد پروفایل کاربری شما.\n"
        "🔸 `/help` - نمایش این پیام راهنما.\n"
        "🔸 `/config` - مدیریت فایل پیکربندی (`config.json`):\n"
        "    - برای دریافت فایل کانفیگ فعلی: ارسال `/config`\n"
        "    - برای به‌روزرسانی کانفیگ: فایل `config.json` ویرایش شده خود را با کپشن `/config` ارسال کنید.\n"
        "🔸 `/upload <type>` - آپلود فایل‌های جانبی (روی فایل مورد نظر ریپلای کنید):\n"
        "    - `<type>` می‌تواند یکی از موارد زیر باشد: `cover`, `signature`, `watermark`, `font`.\n"
        "    - مثال: روی یک عکس ریپلای کنید و بنویسید `/upload cover`.\n"
        "    - *توجه: ذخیره و استفاده کامل از این فایل‌ها در مراحل بعدی تکمیل می‌شود.*\n"
        "\n"
        "🎧 **ارسال فایل صوتی:**\n"
        "   - هر فایل صوتی که برای ربات ارسال کنید، ابتدا بررسی می‌شود:\n"
        "   - اگر MP3 نباشد، به فرمت MP3 (با بیت‌ریت 192k) تبدیل شده و برای شما ارسال می‌شود.\n"
        "   - اگر MP3 باشد، خود فایل برای شما ارسال می‌شود.\n"
        "   - *در آینده، پس از این مرحله، پردازش‌های تعریف شده در `config.json` شما روی فایل MP3 اعمال خواهد شد.*\n"
        "\n"
        "⚙️ **دستورات ادمین (مخصوص ادمین‌ها):**\n"
        "🔸 `/admin add <user_id>` - افزودن موقت یک کاربر به لیست ادمین‌ها.\n"
        "🔸 `/admin del <user_id>` - حذف موقت یک کاربر از لیست ادمین‌ها.\n"
        "\n"
        "📄 **فایل `config.json`:**\n"
        "   - این فایل شامل تمام تنظیمات شما برای پردازش موزیک است.\n"
        "   - برای مشاهده ساختار اولیه، از `/config` استفاده کنید و فایل دریافتی را بررسی نمایید.\n"
        "   - توضیحات کامل در مورد نحوه ویرایش و استفاده از متغیرها به زودی به این راهنما اضافه خواهد شد.\n\n"
        "به زودی قابلیت‌های بیشتری اضافه خواهد شد!"
    )
    await message.reply_text(help_text, disable_web_page_preview=True)

@app.on_message(filters.command("config"))
async def config_command(client: Client, message: Message):
    """Handles the /config command for downloading and updating user configuration."""
    user_id = message.from_user.id
    ensure_user_setup(user_id) # Ensure user directory and config exist
    user_config_path = get_user_config_path(user_id)

    if message.document and message.caption and message.caption.lower().strip() == "/config":
        # User is uploading a new config
        if message.document.file_name.lower() != "config.json":
            await message.reply_text("لطفا یک فایل با نام `config.json` آپلود کنید.")
            return

        try:
            temp_download_path = await client.download_media(message.document, file_name=os.path.join(get_user_data_dir(user_id), "temp_config.json"))
            # Basic validation (check if it's valid JSON)
            with open(temp_download_path, 'r') as f:
                new_config_data = json.load(f)

            # Overwrite the existing config
            os.replace(temp_download_path, user_config_path)
            # Update user_id in the new config, just in case it was changed or missing
            new_config_data["user_id"] = user_id
            with open(user_config_path, 'w') as f:
                json.dump(new_config_data, f, indent=2)

            logger.info(f"User {user_id} updated their config.json")
            await message.reply_text("✅ فایل `config.json` شما با موفقیت به‌روزرسانی شد.")
        except json.JSONDecodeError:
            await message.reply_text("خطا: فایل `config.json` آپلود شده معتبر نیست (JSON format error). لطفا فایل را بررسی و دوباره تلاش کنید.")
            if os.path.exists(temp_download_path):
                os.remove(temp_download_path)
        except Exception as e:
            logger.error(f"Error updating config for user {user_id}: {e}")
            await message.reply_text(f"خطایی هنگام به‌روزرسانی کانفیگ رخ داد: {e}")
            if os.path.exists(temp_download_path) and temp_download_path != user_config_path : # ensure we don't delete the original if paths are same
                 os.remove(temp_download_path)
    elif len(message.command) == 1 : # Just /config, user wants to download
        if os.path.exists(user_config_path):
            try:
                await message.reply_document(
                    document=user_config_path,
                    caption="این فایل `config.json` فعلی شماست.\nمی‌توانید آن را ویرایش کرده و با دستور `/config` (به عنوان کپشن فایل) دوباره ارسال کنید تا تنظیمات به‌روز شوند."
                )
                logger.info(f"Sent config.json to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending config to user {user_id}: {e}")
                await message.reply_text(f"خطایی هنگام ارسال فایل کانفیگ رخ داد: {e}")
        else:
            # This case should ideally not happen if ensure_user_setup works correctly
            await message.reply_text("فایل `config.json` شما یافت نشد. لطفا ابتدا دستور /start را اجرا کنید.")
            logger.warning(f"config.json not found for user {user_id} on /config command, though ensure_user_setup should prevent this.")
    else:
        await message.reply_text(
            "برای دریافت فایل کانفیگ، فقط `/config` را ارسال کنید.\n"
            "برای به‌روزرسانی، فایل `config.json` خود را با کپشن `/config` ارسال نمایید."
        )

@app.on_message(filters.command("upload"))
async def upload_command(client: Client, message: Message):
    """Handles the /upload command for various file types."""
    user_id = message.from_user.id
    ensure_user_setup(user_id) # Ensure user directory exists
    
    args = message.command[1:]
    upload_type = None
    if args:
        upload_type = args[0].lower()

    if not message.reply_to_message or not message.reply_to_message.document:
        if not upload_type:
             await message.reply_text(
                "لطفا برای آپلود، روی یک فایل ریپلای کنید و دستور `/upload <نوع_فایل>` را بنویسید.\n"
                "مثال: `/upload cover` (باید روی یک عکس ریپلای شده باشد)\n\n"
                "انواع فایل مجاز:\n"
                "▫️ `cover`: برای آپلود کاور موزیک (عکس).\n"
                "▫️ `signature`: برای آپلود امضای صوتی (فایل صوتی).\n"
                "▫️ `watermark`: برای آپلود تصویر واترمارک (عکس).\n"
                "▫️ `font`: برای آپلود فونت (فایل .ttf یا .otf)."
            )
        else:
            await message.reply_text(
                f"لطفا برای آپلود `{upload_type}`، روی فایل مربوطه ریپلای کرده و دستور `/upload {upload_type}` را مجددا ارسال کنید."
            )
        return

    # At this point, user has replied to a document and potentially provided a type
    # Further logic for handling specific file types and saving them will be added in later steps.
    # For now, we just acknowledge.

    if upload_type:
        await message.reply_text(
            f"درخواست آپلود برای `{upload_type}` دریافت شد.\n"
            f"نام فایل: `{message.reply_to_message.document.file_name}`\n\n"
            "⚠️ توجه: قابلیت ذخیره و استفاده از فایل‌های آپلود شده در مراحل بعدی پیاده‌سازی خواهد شد."
        )
        logger.info(f"/upload command for type '{upload_type}' from user {user_id}, file: {message.reply_to_message.document.file_name}")
    else:
        await message.reply_text(
            "شما روی یک فایل ریپلای کردید، اما نوع آپلود را مشخص نکرده‌اید.\n"
            "لطفا نوع فایل را مشخص کنید. مثال: `/upload cover`\n\n"
            "انواع فایل مجاز: `cover`, `signature`, `watermark`, `font`."
        )
        logger.info(f"/upload command (no type specified) from user {user_id}, file: {message.reply_to_message.document.file_name}")

# --- Music Handling ---
@app.on_message(filters.audio)
async def audio_handler(client: Client, message: Message):
    """Handles incoming audio files for processing."""
    user_id = message.from_user.id
    ensure_user_setup(user_id)
    logger.info(f"Received audio from user {user_id}. File ID: {message.audio.file_id}")

    if not message.audio:
        logger.warning(f"No audio attribute in message from user {user_id}")
        await message.reply_text("فایل صوتی معتبر نیست.")
        return

    file_name = message.audio.file_name
    if not file_name:
        file_name = f"{message.audio.file_unique_id}.{message.audio.mime_type.split('/')[-1]}" if message.audio.mime_type else f"{message.audio.file_unique_id}.unknown"
    
    original_file_path = os.path.join(get_user_data_dir(user_id), f"original_{file_name}")
    
    try:
        status_msg = await message.reply_text("در حال دانلود فایل صوتی...")
        await client.download_media(message.audio, file_name=original_file_path)
        logger.info(f"Downloaded audio for {user_id} to {original_file_path}")
        await status_msg.edit_text("دانلود کامل شد. در حال بررسی فرمت...")

        # Step 3: Convert to MP3 if not already MP3
        output_mp3_path = original_file_path
        is_mp3 = file_name.lower().endswith(".mp3") or message.audio.mime_type == "audio/mpeg"

        if not is_mp3:
            await status_msg.edit_text("فرمت MP3 نیست. در حال تبدیل به MP3...")
            base, ext = os.path.splitext(original_file_path)
            output_mp3_path = f"{base}.mp3"
            
            try:
                logger.info(f"Converting {original_file_path} to MP3 for user {user_id}")
                (
                    ffmpeg
                    .input(original_file_path)
                    .output(output_mp3_path, acodec='libmp3lame', audio_bitrate='192k') # Example bitrate
                    .overwrite_output()
                    .run(cmd_path()) # Use cmd_path helper
                )
                logger.info(f"Converted to MP3: {output_mp3_path} for user {user_id}")
                await status_msg.edit_text("تبدیل به MP3 کامل شد. در حال ارسال...")
                
                # Send the converted MP3
                await client.send_audio(
                    chat_id=message.chat.id,
                    audio=output_mp3_path,
                    caption=f"تبدیل شده به MP3: {os.path.basename(output_mp3_path)}\n(پردازش‌های بیشتر در مراحل بعدی اضافه خواهند شد)",
                    reply_to_message_id=message.id
                )
                await status_msg.delete()
                if original_file_path != output_mp3_path: # if conversion happened, delete original non-mp3
                    os.remove(original_file_path)
                # For now, we also remove the converted MP3 after sending as it's just an intermediate step
                # In the full pipeline, this file would be the input for further processing.
                os.remove(output_mp3_path) 
                return # Stop here for this step of the plan

            except ffmpeg.Error as e:
                logger.error(f"FFmpeg conversion error for user {user_id}: {e.stderr.decode('utf8') if e.stderr else str(e)}")
                await status_msg.edit_text(f"خطا در تبدیل به MP3: {e.stderr.decode('utf8') if e.stderr else str(e)}")
                if os.path.exists(original_file_path): # Clean up original if conversion failed
                    os.remove(original_file_path)
                return
            except Exception as e:
                logger.error(f"Unexpected error during conversion for user {user_id}: {str(e)}")
                await status_msg.edit_text(f"یک خطای غیرمنتظره در تبدیل به MP3 رخ داد.")
                if os.path.exists(original_file_path): # Clean up original if conversion failed
                    os.remove(original_file_path)
                return

        else: # Already MP3
            await status_msg.edit_text("فایل در فرمت MP3 است. (پردازش‌های بیشتر در مراحل بعدی اضافه خواهند شد)")
            # For now, just acknowledge. In future, this 'output_mp3_path' would feed into the next processing stage.
            # We'll send it back for now to show it's handled.
            await client.send_audio(
                chat_id=message.chat.id,
                audio=original_file_path, # Send the original MP3
                caption=f"فایل MP3 دریافت شد: {os.path.basename(original_file_path)}\n(پردازش‌های بیشتر در مراحل بعدی اضافه خواهند شد)",
                reply_to_message_id=message.id
            )
            await status_msg.delete()
            os.remove(original_file_path) # Clean up after sending
            return

    except Exception as e:
        logger.error(f"Error processing audio for user {user_id}: {e}")
        if 'status_msg' in locals() and status_msg:
             await status_msg.edit_text(f"خطایی در پردازش فایل صوتی رخ داد: {e}")
        else:
            await message.reply_text(f"خطایی در پردازش فایل صوتی رخ داد: {e}")
        if os.path.exists(original_file_path): # General cleanup
            os.remove(original_file_path)
        if 'output_mp3_path' in locals() and os.path.exists(output_mp3_path) and output_mp3_path != original_file_path:
            os.remove(output_mp3_path)

def check_ffmpeg():
    """Checks if ffmpeg is installed and accessible."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logger.info("ffmpeg found.")
        return True
    except FileNotFoundError:
        logger.error("ffmpeg not found. Please install ffmpeg and ensure it's in your PATH.")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg found but there was an error running it: {e}")
        return False # Or True, depending on if you want to proceed with a potentially broken ffmpeg

FFMPEG_PATH = "ffmpeg" # Default, assuming ffmpeg is in PATH

def cmd_path() -> str:
    """Returns the path to the ffmpeg executable."""
    # This could be enhanced to find ffmpeg if not in PATH or allow user to specify
    return FFMPEG_PATH

# --- Admin Commands ---
def is_admin(user_id: int) -> bool:
    """Checks if a user is an admin."""
    return user_id in ADMIN_USER_IDS

@app.on_message(filters.command("admin") & filters.private)
async def admin_command_handler(client: Client, message: Message):
    """Handles /admin commands for adding/removing admins."""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.reply_text("شما اجازه استفاده از این دستور را ندارید.")
        logger.warning(f"Non-admin user {user_id} attempted to use /admin command.")
        return

    command_parts = message.text.split()
    if len(command_parts) < 3:
        await message.reply_text("استفاده صحیح: `/admin <add|del> <user_id>`")
        return

    action = command_parts[1].lower()
    try:
        target_user_id = int(command_parts[2])
    except ValueError:
        await message.reply_text("`<user_id>` باید یک عدد صحیح باشد.")
        return

    if action == "add":
        # Placeholder: In a real scenario, you'd add this to a persistent store
        if target_user_id not in ADMIN_USER_IDS:
            ADMIN_USER_IDS.append(target_user_id) # Modifying global list for now
            await message.reply_text(f"کاربر {target_user_id} به لیست ادمین‌ها (موقت) اضافه شد.")
            logger.info(f"Admin {user_id} added {target_user_id} to admin list (session only).")
        else:
            await message.reply_text(f"کاربر {target_user_id} در حال حاضر در لیست ادمین‌ها قرار دارد.")
    elif action == "del":
        # Placeholder: In a real scenario, you'd remove this from a persistent store
        if target_user_id in ADMIN_USER_IDS:
            ADMIN_USER_IDS.remove(target_user_id) # Modifying global list for now
            await message.reply_text(f"کاربر {target_user_id} از لیست ادمین‌ها (موقت) حذف شد.")
            logger.info(f"Admin {user_id} removed {target_user_id} from admin list (session only).")
        else:
            await message.reply_text(f"کاربر {target_user_id} در لیست ادمین‌ها وجود ندارد.")
    else:
        await message.reply_text("عمل نامعتبر. از `add` یا `del` استفاده کنید.")

async def main():
    """Main function to start the bot."""
    if not check_ffmpeg():
        logger.error("Exiting due to ffmpeg not being available.")
        return
    logger.info("Starting bot...")
    await app.start()
    logger.info("Bot started successfully!")
    # Keep the bot running
    await app.idle()
    logger.info("Bot stopped.")

if __name__ == "__main__":
    # Make sure to set your API_ID, API_HASH, and BOT_TOKEN environment variables
    # or replace the placeholder values above.
    if API_ID == 12345 or API_HASH == "your_api_hash" or BOT_TOKEN == "your_bot_token":
        logger.warning("API_ID, API_HASH, or BOT_TOKEN are set to default placeholders.")
        logger.warning("Please update them in the script or via environment variables.")
    
    app.run(main())
