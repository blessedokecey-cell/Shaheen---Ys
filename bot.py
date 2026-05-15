import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant

# --- إعدادات البوت (تُجلب من متغيرات البيئة في Railway) ---
API_ID = int(os.environ.get("API_ID", 1234567))        
API_HASH = os.environ.get("API_HASH", "abcdefg")   
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token") 
DEVELOPER_ID = int(os.environ.get("DEVELOPER_ID", 12345678))  
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "my_channel") 

# روابط الوسائط
WELCOME_PHOTO = os.environ.get("WELCOME_PHOTO", "https://unsplash.com") 
WELCOME_AUDIO = os.environ.get("WELCOME_AUDIO", "https://soundhelix.com") 
DEV_AUDIO = os.environ.get("DEV_AUDIO", "https://soundhelix.com") 

app = Client("controller_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# دالة التحقق من الإشتراك الإجباري
async def check_sub(client: Client, message: Message):
    # إزالة الـ @ إذا وجدت لتجنب أخطاء الرابط
    clean_username = CHANNEL_USERNAME.replace("@", "")
    try:
        await client.get_chat_member(CHANNEL_USERNAME, message.from_user.id)
        return True
    except UserNotParticipant:
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("اضغط هنا للإشتراك بالقناة 📢", url=f"https://t.me/{clean_username}"),
            InlineKeyboardButton("تحقق من الإشتراك 🔄", callback_data="check_again")
        ]])
        await message.reply_text(
            f"⚠️ عذراً عزيزي {message.from_user.mention}، يجب عليك الإشتراك في القناة أولاً لتتمكن من استخدام البوت.",
            reply_markup=btn
        )
        return False
    except Exception:
        # في حال وجود خطأ تقني (مثل البوت ليس مشرفاً) يتم السماح للمستخدم بالمرور
        return True

@app.on_message(filters.private & filters.command("start"))
async def start_command(client: Client, message: Message):
    if not await check_sub(client, message):
        return
        
    main_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إنشاء منشور جديد", callback_data="create_post"),
         InlineKeyboardButton("📢 عرض القنوات", callback_data="view_channels")],
        [InlineKeyboardButton("👨‍💻 مطور البوت", callback_data="dev_info")]
    ])
    
    await client.send_photo(
        chat_id=message.chat.id, 
        photo=WELCOME_PHOTO, 
        caption=f"👋 أهلاً بك يا {message.from_user.mention} في بوت التحكم بالمنشورات.\n\n🤖 يمكنك إدارة قنواتك وصنع منشورات احترافية بأزرار شفافة.", 
        reply_markup=main_buttons
    )
    
    await client.send_audio(
        chat_id=message.chat.id, 
        audio=WELCOME_AUDIO, 
        caption="🎵 نغمة الترحيب"
    )

@app.on_callback_query()
async def callback_handler(client: Client, query):
    user_id = query.from_user.id
    
    if query.data == "check_again":
        try:
            await client.get_chat_member(CHANNEL_USERNAME, user_id)
            await query.answer("✅ تم التحقق من الإشتراك!", show_alert=True)
            await query.message.delete()
            # استدعاء Start مجدداً كرسالة وهمية
            from pyrogram.types import User, Chat
            fake_msg = query.message
            fake_msg.from_user = query.from_user
            await start_command(client, fake_msg)
        except UserNotParticipant:
            await query.answer("❌ لم تشترك بعد!", show_alert=True)
        return

    if query.data == "view_channels":
        channels_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_main")]])
        await query.message.edit_caption(
            caption=f"📢 **القنوات المتصلة:**\n\n1️⃣ القناة الإجبارية: @{CHANNEL_USERNAME}\n💡 لإضافة قنوات، ارفع البوت مشرفاً ووجه رسالة منها.", 
            reply_markup=channels_btn
        )

    elif query.data == "dev_info":
        dev_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 تواصل مع المطور", url=f"tg://user?id={DEVELOPER_ID}")],
            [InlineKeyboardButton("🔙 العودة", callback_data="back_main")]
        ])
        await query.message.edit_caption(
            caption=f"📋 **بطاقة المطور:**\n\n🆔 الآيدي: `{DEVELOPER_ID}`\n🛠️ اللغة: Python (Pyrogram)", 
            reply_markup=dev_btn
        )
        await client.send_audio(chat_id=query.message.chat.id, audio=DEV_AUDIO)

    elif query.data == "back_main":
        main_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ إنشاء منشور جديد", callback_data="create_post"), 
             InlineKeyboardButton("📢 عرض القنوات", callback_data="view_channels")],
            [InlineKeyboardButton("👨‍💻 مطور البوت", callback_data="dev_info")]
        ])
        await query.message.edit_caption(
            caption="👋 أهلاً بك مجدداً في قائمة التحكم.\n🤖 اختر ما تريد القيام به:", 
            reply_markup=main_buttons
        )

    elif query.data == "create_post":
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_main")]])
        await query.message.edit_caption(
            caption="📝 أرسل الآن نص المنشور الذي تريد إنشائه:", 
            reply_markup=back_btn
        )

if __name__ == "__main__":
    print("⚡ البوت يعمل الآن...")
    app.run()
        
