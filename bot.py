import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant

# --- إعدادات البوت (جلب البيانات تلقائياً من المنصة أو ضعها هنا مباشرة) ---
API_ID = int(os.environ.get("API_ID", 1234567))        
API_HASH = os.environ.get("API_HASH", "abcdefg")   
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token") 
DEVELOPER_ID = int(os.environ.get("DEVELOPER_ID", 12345678))  
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "my_channel") 

WELCOME_PHOTO = "https://unsplash.com" 
WELCOME_AUDIO = "https://soundhelix.com" 
DEV_AUDIO = "https://soundhelix.com" 

app = Client("controller_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def check_sub(client: Client, message: Message):
    try:
        await client.get_chat_member(CHANNEL_USERNAME, message.from_user.id)
        return True
    except UserNotParticipant:
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("اضغط هنا للإشتراك بالقناة 📢", url=f"https://t.me{CHANNEL_USERNAME}"),
            InlineKeyboardButton("تحقق من الإشتراك 🔄", callback_data="check_again")
        ]])
        await message.reply_text(
            f"⚠️ عذراً عزيزي {message.from_user.mention}، يجب عليك الإشتراك في القناة أولاً لتتمكن من استخدام البوت.",
            reply_markup=btn
        )
        return False
    except Exception:
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
    await client.send_photo(chat_id=message.chat.id, photo=WELCOME_PHOTO, caption=f"👋 أهلاً بك يا {message.from_user.mention} في بوت التحكم بالمنشورات.\n\n🤖 يمكنك من خلال البوت إدارة قنواتك وصنع منشورات احترافية بأزرار شفافة.", reply_markup=main_buttons)
    await client.send_audio(chat_id=message.chat.id, audio=WELCOME_AUDIO, caption="🎵 نغمة الترحيب بالبوت")

@app.on_callback_query()
async def callback_handler(client: Client, query):
    user_id = query.from_user.id
    if query.data == "check_again":
        try:
            await client.get_chat_member(CHANNEL_USERNAME, user_id)
            await query.answer("✅ شكراً لك على الإشتراك! تم تفعيل البوت.", show_alert=True)
            await query.message.delete()
            fake_msg = Message(from_user=query.from_user, chat=query.message.chat)
            await start_command(client, fake_msg)
        except UserNotParticipant:
            await query.answer("❌ لم تشترك في القناة بعد، يرجى الإشتراك أولاً.", show_alert=True)
        return
    if query.data == "view_channels":
        channels_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_main")]])
        await query.message.edit_caption(caption=f"📢 **القنوات المتصلة بالبوت حالياً:**\n\n1️⃣ القناة الإجبارية: @{CHANNEL_USERNAME}\n💡 لإضافة قنوات جديدة، قم برفع البوت مشرفاً في قناتك ثم أرسل توجيه من القناة إلى هنا.", reply_markup=channels_btn)
    elif query.data == "dev_info":
        dev_btn = InlineKeyboardMarkup([[InlineKeyboardButton("💬 تواصل مع المطور", url=f"tg://user?id={DEVELOPER_ID}")],[InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_main")]])
        await query.message.edit_caption(caption=f"📋 **البطاقة التعريفية لمطور البوت:**\n\n👤 **المطور:** المبرمج المسؤول\n🆔 **الآيدي الخاص به:** `{DEVELOPER_ID}`\n🛠️ **اللغة المستخدمة:** Python (Pyrogram)\n\n📩 يمكنك الضغط على الزر أدناه للتواصل المباشر مع المطور.", reply_markup=dev_btn)
        await client.send_audio(chat_id=query.message.chat.id, audio=DEV_AUDIO, caption="🎵 المقطع الصوتي الخاص بالمطور")
    elif query.data == "back_main":
        main_buttons = InlineKeyboardMarkup([[InlineKeyboardButton("➕ إنشاء منشور جديد", callback_data="create_post"), InlineKeyboardButton("📢 عرض القنوات", callback_data="view_channels")],[InlineKeyboardButton("👨‍💻 مطور البوت", callback_data="dev_info")]])
        await query.message.edit_caption(caption=f"👋 أهلاً بك مجدداً في قائمة التحكم بالمنشورات.\n\n🤖 اختر ما تريد القيام به من الأزرار أدناه:", reply_markup=main_buttons)
    elif query.data == "create_post":
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_main")]])
        await query.message.edit_caption(caption="📝 **أرسل الآن نص المنشور الذي تريد إنشائه:**\n\nيمكنك استخدام التنسيقات مثل *الخط العريض* أو _المائل_، وسيطلب منك البوت لاحقاً إضافة الأزرار الشفافة.", reply_markup=back_btn)

if __name__ == "__main__":
    print("⚡ البوت يعمل الآن بنجاح...")
    app.run()
    
