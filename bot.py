import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant

# --- إعدادات البوت (ضع بياناتك هنا) ---
API_ID = 1234567        # استبدله بـ API ID الخاص بك من my.telegram.org
API_HASH = "abcdefg"   # استبدله بـ API HASH الخاص بك
BOT_TOKEN = "your_bot_token" # توكن البوت من BotFather
DEVELOPER_ID = 12345678  # آيدي حسابك المطور (الأرقام فقط)
CHANNEL_USERNAME = "my_channel" # يوزر قناتك للإشتراك الإجباري (بدون @)

# --- روابط الوسائط للترحيب والمطور ---
WELCOME_PHOTO = "https://unsplash.com" # رابط صورة الترحيب
WELCOME_AUDIO = "https://soundhelix.com" # رابط صوت الترحيب
DEV_AUDIO = "https://soundhelix.com" # رابط صوت المطور

app = Client("controller_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# دالة التحقق من الإشتراك الإجباري
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
        # في حال لم يكن البوت مشرفاً بالقناة سيتخطى التحقق لمنع توقف البوت
        return True

# أمر البداية /start والترحيب
@app.on_message(filters.private & filters.command("start"))
async def start_command(client: Client, message: Message):
    if not await check_sub(client, message):
        return

    # الأزرار الرئيسية للبوت (مطابقة لـ Controllerbot)
    main_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إنشاء منشور جديد", callback_data="create_post"),
         InlineKeyboardButton("📢 عرض القنوات", callback_data="view_channels")],
        [InlineKeyboardButton("👨‍💻 مطور البوت", callback_data="dev_info")]
    ])

    # إرسال صورة الترحيب
    await client.send_photo(
        chat_id=message.chat.id,
        photo=WELCOME_PHOTO,
        caption=f"👋 أهلاً بك يا {message.from_user.mention} في بوت التحكم بالمنشورات والتعليقات.\n\n"
                f"🤖 يمكنك من خلال البوت إدارة قنواتك وصنع منشورات احترافية بأزرار شفافة.",
        reply_markup=main_buttons
    )
    
    # إرسال المقطع الصوتي الترحيبي
    await client.send_audio(
        chat_id=message.chat.id,
        audio=WELCOME_AUDIO,
        caption="🎵 نغمة الترحيب بالبوت"
    )

# معالجة ضغطات الأزرار (Callback Queries)
@app.on_callback_query()
async def callback_handler(client: Client, query):
    user_id = query.from_user.id
    
    # تحقق الإشتراك عند الضغط على زر التحديث
    if query.data == "check_again":
        try:
            await client.get_chat_member(CHANNEL_USERNAME, user_id)
            await query.answer("✅ شكراً لك على الإشتراك! تم تفعيل البوت.", show_alert=True)
            await query.message.delete()
            # إرجاع المستخدم لرسالة البداية
            fake_msg = Message(from_user=query.from_user, chat=query.message.chat)
            await start_command(client, fake_msg)
        except UserNotParticipant:
            await query.answer("❌ لم تشترك في القناة بعد، يرجى الإشتراك أولاً.", show_alert=True)
        return

    # زر عرض القنوات
    if query.data == "view_channels":
        channels_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_main")]])
        await query.message.edit_caption(
            caption=f"📢 **القنوات المتصلة بالبوت حالياً:**\n\n"
                    f"1️⃣ القناة الإجبارية: @{CHANNEL_USERNAME}\n"
                    f"💡 لإضافة قنوات جديدة، قم برفع البوت مشرفاً في قناتك ثم أرسل توجيه من القناة إلى هنا.",
            reply_markup=channels_btn
        )

    # زر المطور والبطاقة التعريفية
    elif query.data == "dev_info":
        dev_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 تواصل مع المطور", url=f"tg://user?id={DEVELOPER_ID}")],
            [InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_main")]
        ])
        
        # إرسال بطاقة تعريفية نصية
        await query.message.edit_caption(
            caption=f"📋 **البطاقة التعريفية لمطور البوت:**\n\n"
                    f"👤 **المطور:** المبرمج المسؤول\n"
                    f"🆔 **الآيدي الخاص به:** `{DEVELOPER_ID}`\n"
                    f"🛠️ **اللغة المستخدمة:** Python (Pyrogram)\n\n"
                    f"📩 يمكنك الضغط على الزر أدناه للتواصل المباشر مع المطور لحل المشاكل أو طلب الإضافات.",
            reply_markup=dev_btn
        )
        
        # إرسال المقطع الصوتي الخاص بالمطور
        await client.send_audio(
            chat_id=query.message.chat.id,
            audio=DEV_AUDIO,
            caption="🎵 المقطع الصوتي الخاص بالمطور"
        )

    # زر العودة للقائمة الرئيسية
    elif query.data == "back_main":
        main_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ إنشاء منشور جديد", callback_data="create_post"),
             InlineKeyboardButton("📢 عرض القنوات", callback_data="view_channels")],
            [InlineKeyboardButton("👨‍💻 مطور البوت", callback_data="dev_info")]
        ])
        await query.message.edit_caption(
            caption=f"👋 أهلاً بك مجدداً في قائمة التحكم بالمنشورات.\n\n"
                    f"🤖 اختر ما تريد القيام به من الأزرار أدناه:",
            reply_markup=main_buttons
        )

    # زر إنشاء منشور (محاكاة ووردبريس/كنترولربوت)
    elif query.data == "create_post":
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_main")]])
        await query.message.edit_caption(
            caption="📝 **أرسل الآن نص المنشور الذي تريد إنشائه:**\n\n"
                    "يمكنك استخدام التنسيقات مثل *الخط العريض* أو _المائل_، وسيطلب منك البوت لاحقاً إضافة الأزرار الشفافة.",
            reply_markup=back_btn
        )

# تشغيل البوت بنجاح
if __name__ == "__main__":
    print("⚡ البوت يعمل الآن على أكمل وجه وبدون أخطاء...")
    app.run()
  
