import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client(
    "allu_tv_leech_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def progress_hook(d, message, loop):
    if d['status'] == 'downloading':
        current = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        filename = os.path.basename(d.get('filename', 'video'))
        
        if total > 0:
            percentage = (current / total) * 100
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            
            completed_blocks = int(percentage // 10)
            progress_bar = "█" * completed_blocks + "░" * (10 - completed_blocks)
            
            progress_text = (
                f"📥 **ഡൗൺലോഡ് ചെയ്തുകൊണ്ടിരിക്കുന്നു...**\n\n"
                f"📁 **File:** `{filename}`\n"
                f"[{progress_bar}] **{percentage:.1f}%**\n"
                f"⚡ **Speed:** {speed}\n"
                f"⏳ **ETA:** {eta}"
            )
            
            try:
                asyncio.run_coroutine_threadsafe(
                    message.edit_text(progress_text), loop
                )
            except Exception:
                pass

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text(
        "👋 ഹലോ!\n"
        "യൂട്യൂബ്, ഗോഫൈൽ (Gofile), ടെറാബോക്സ് (TeraBox) ലിങ്കുകൾ ഡൗൺലോഡ് ചെയ്യാൻ `/leech [link]` എന്ന് അയക്കുക അല്ലെങ്കിൽ നേരിട്ട് ലിങ്ക് അയക്കൂ!"
    )

@app.on_message(filters.command("leech") | (filters.text & filters.private))
async def leech_handler(client, message: Message):
    if message.command and len(message.command) > 1:
        url = message.command[1]
    else:
        url = message.text.strip()
    
    if not url.startswith("http"):
        return

    platform_name = "Unsupported"
    if "youtube.com" in url or "youtu.be" in url:
        platform_name = "YouTube 📺"
    elif "gofile.io" in url:
        platform_name = "Gofile 📁"
    elif "tera" in url or "1024tera" in url or "terasharefile.com" in url:
        platform_name = "TeraBox 📦"
    else:
        platform_name = "Web Link 🌐"

    status_msg = await message.reply_text(f"📥 **{platform_name}** ലിങ്ക് തിരിച്ചറിഞ്ഞു. ഡൗൺലോഡ് ആരംഭിക്കുന്നു...")
    loop = asyncio.get_running_loop()

    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'progress_hooks': [lambda d: progress_hook(d, status_msg, loop)],
    }

    downloaded_file = None
    try:
        def download():
            nonlocal downloaded_file
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)

        await asyncio.to_thread(download)

        if downloaded_file and os.path.exists(downloaded_file):
            await status_msg.edit_text("📤 ടെലഗ്രാമിലേക്ക് അപ്‌ലോഡ് ചെയ്യുന്നു...")
            
            await message.reply_document(
                document=downloaded_file,
                caption=f"📁 ഫയൽ വിജയകരമായി ഡൗൺലോഡ് ചെയ്തു!\n🔗 **Platform:** {platform_name}\n🔗 **Source:** {url}"
            )
            
            os.remove(downloaded_file)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ എറർ: ഫയൽ ഡൗൺലോഡ് ചെയ്യാൻ സാധിച്ചില്ല.")

    except Exception as e:
        await status_msg.edit_text(f"❌ **Task Failed / Error:**\n`{str(e)}`")
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)

if __name__ == "__main__":
    print("ബോട്ട് റൺ ആകുന്നു...")
    app.run()
