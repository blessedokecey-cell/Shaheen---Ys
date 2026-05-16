import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import SchedulerDatabase

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db_manager = SchedulerDatabase()
post_scheduler = AsyncIOScheduler()

# آلة الحالات لمحاكاة مراحل ControllerBot
class ControllerStates(StatesGroup):
    waiting_for_channel_id = State()
    waiting_for_post_content = State()
    waiting_for_inline_buttons = State()
    waiting_for_schedule_time = State()

# --- 📋 القوائم الرئيسية وهيكل الأزرار المطور ---

def get_main_menu():
    """القائمة الرئيسية الشبيهة بـ ControllerBot"""
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📝 إنشاء منشور جديد", callback_data="create_post")],
        [types.InlineKeyboardButton(text="📅 المنشورات المجدولة", callback_data="view_scheduled")],
        [types.InlineKeyboardButton(text="📢 إدارة القنوات المرتبطة", callback_data="manage_channels")]
    ])

def get_post_creation_menu():
    """قائمة خيارات التعديل على المنشور قبل النشر"""
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔗 إضافة أزرار الرابط (URL)", callback_data="add_url_buttons")],
        [types.InlineKeyboardButton(text="🚀 نشر الآن", callback_data="publish_now")],
        [types.InlineKeyboardButton(text="⏱️ جدولة المنشور", callback_data="schedule_post")],
        [types.InlineKeyboardButton(text="❌ إلغاء المنشور", callback_data="cancel_creation")]
    ])

# --- 🚀 معالجة الأوامر والوظائف التفاعلية ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """أمر البدء وفتح لوحة التحكم الذكية"""
    if not os.path.exists("users"):
        os.makedirs("users")
        
    user_id_str = str(message.from_user.id)
    with open(f"users/{user_id_str}.json", "w") as f:
        f.write("{}")

    await message.answer(
        text="🤖 **أهلاً بك في لوحة تحكم ControllerBot المطور!**\n\n"
             "هذا البوت يتيح لك إدارة قنواتك، صناعة منشورات احترافية مزودة بأزرار روابط، وجدولتها للنشر التلقائي بكفاءة عالية.\n"
             "يرجى اختيار أحد الأوامر من القائمة أدناه البدء:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(lambda call: call.data == "manage_channels")
async def manage_channels(call: types.CallbackQuery):
    """عرض القنوات وإتاحة خيار الربط"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ ربط قناة جديدة", callback_data="add_new_channel")],
        [types.InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]
    ])
    await call.message.edit_text(
        text="📢 **إدارة القنوات المرتبطة:**\n\n"
             "تأكد أولاً من رفع البوت كمسؤول (Admin) في قناتك مع صلاحية 'نشر الرسائل' ليعمل النظام بكفاءة حتمية.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda call: call.data == "create_post")
@dp.callback_query(lambda call: call.data == "add_new_channel")
async def request_channel_id(call: types.CallbackQuery, state: FSMContext):
    """طلب معرف القناة المستهدفة"""
    await call.message.answer("📢 من فضلك قم بإرسال معرف القناة (مثال: `@MyChannel`):", parse_mode="Markdown")
    await state.set_state(ControllerStates.waiting_for_channel_id)
    await call.answer()

@dp.message(ControllerStates.waiting_for_channel_id)
async def process_channel_id(message: types.Message, state: FSMContext):
    """حفظ القناة وطلب نص أو محتوى المنشور"""
    channel_id = message.text.strip()
    if not channel_id.startswith("@"):
        await message.answer("❌ معرف القناة خاطئ! يجب أن يبدأ بالعلامة @")
        return
    await state.update_data(target_channel=channel_id)
    await message.answer("📝 **رائع! الآن أرسل محتوى المنشور الخاص بك:**\n(يدعم النصوص، التنسيق، الروابط المدمجة وغيرها)")
    await state.set_state(ControllerStates.waiting_for_post_content)

@dp.message(ControllerStates.waiting_for_post_content)
async def process_post_content(message: types.Message, state: FSMContext):
    """عرض المنشور وفتح خيارات التعديل والنشر الشبيهة بـ ControllerBot"""
    await state.update_data(post_text=message.text)
    user_data = await state.get_data()
    
    await message.answer(
        text=f"👁️ **معاينة المنشور الموجه إلى ({user_data['target_channel']}):**\n\n{message.text}",
        reply_markup=get_post_creation_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(lambda call: call.data == "add_url_buttons")
async def request_url_buttons(call: types.CallbackQuery, state: FSMContext):
    """طلب إضافة أزرار الروابط التفاعلية أسفل المنشور"""
    await call.message.answer(
        text="🔗 **إضافة أزرار روابط للمنشور:**\n\n"
             "يرجى إرسال الأزرار بالصيغة القياسية التالية:\n"
             "`اسم الزر - رابط الزر`\n\n"
             "مثال:\n"
             "`تابعنا هنا - https://google.com`",
        parse_mode="Markdown"
    )
    await state.set_state(ControllerStates.waiting_for_inline_buttons)
    await call.answer()

@dp.message(ControllerStates.waiting_for_inline_buttons)
async def process_inline_buttons(message: types.Message, state: FSMContext):
    """معالجة الأزرار وصناعة المعاينة الجديدة للمنشور"""
    try:
        raw_text = message.text.strip()
        if " - " not in raw_text:
            await message.answer("❌ الصيغة خاطئة! يرجى إدخال: اسم الزر - الرابط")
            return
            
        btn_name, btn_url = raw_text.split(" - ")
        inline_kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=btn_name.strip(), url=btn_url.strip())]
        ])
        
        await state.update_data(has_buttons=True, btn_name=btn_name.strip(), btn_url=btn_url.strip())
        user_data = await state.get_data()
        
        await message.answer(
            text=f"👁️ **المعاينة النهائية للمنشور بالأزرار الروابط:**\n\n{user_data['post_text']}",
            reply_markup=get_post_creation_menu(),
            parse_mode="Markdown"
        )
    except Exception:
        await message.answer("❌ حدث خطأ أثناء فحص الرابط والتنسيق المرفق.")

@dp.callback_query(lambda call: call.data == "publish_now")
async def publish_now(call: types.CallbackQuery, state: FSMContext):
    """النشر الفوري في القناة التلغرام"""
    user_data = await state.get_data()
    try:
        reply_markup = None
        if user_data.get("has_buttons"):
            reply_markup = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text=user_data["btn_name"], url=user_data["btn_url"])]
            ])
            
        await bot.send_message(chat_id=user_data['target_channel'], text=user_data['post_text'], reply_markup=reply_markup, parse_mode="Markdown")
        await call.message.answer("🚀 **تم نشر المنشور الخاص بك في القناة بنجاح واحترافية تامة!**")
        await state.clear()
    except Exception as e:
        await call.message.answer(f"❌ فشل النشر! تأكد من وجود البوت كأدمن في القناة المرتبطة. الخطأ: {e}")
    await call.answer()

@dp.callback_query(lambda call: call.data == "schedule_post")
async def request_schedule_time(call: types.CallbackQuery, state: FSMContext):
    """طلب تحديد وقت وتاريخ الجدولة"""
    await call.message.answer(
        text="⏱️ **جدولة وقت النشر التلقائي:**\n\n"
             "يرجى إرسال التوقيت بصيغة النظام القياسية التالية:\n"
             "`YYYY-MM-DD HH:MM:SS`\n\n"
             "مثال:\n"
             "`2026-06-15 14:30:00`",
        parse_mode="Markdown"
    )
    await state.set_state(ControllerStates.waiting_for_schedule_time)
    await call.answer()

@dp.message(ControllerStates.waiting_for_schedule_time)
async def process_schedule_time(message: types.Message, state: FSMContext):
    """حفظ المنشور المجدول في قاعدة البيانات الذكية"""
    try:
        raw_time = message.text.strip()
        parsed_datetime = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
        
        if parsed_datetime <= datetime.now():
            await message.answer("❌ خطأ: الوقت المحدد يجب أن يكون في المستقبل!")
            return
            
        user_data = await state.get_data()
        
        # تخزين البيانات في الجداول لقذفها تلقائياً بالخلفية
        db_manager.add_scheduled_post(
            channel_id=user_data['target_channel'],
            post_text=user_data['post_text'],
            scheduled_time=parsed_datetime
        )
        
        await message.answer(f"✅ **تمت الجدولة بنجاح على طريقة ControllerBot!**\n⏳ سيتم النشر التلقائي في: {raw_time}")
        await state.clear()
    except ValueError:
        await message.answer("❌ صيغة الوقت خاطئة! تأكد من مطابقتها للمثال المعروض تماماً.")

@dp.callback_query(lambda call: call.data == "view_scheduled")
async def view_scheduled(call: types.CallbackQuery):
    """استعراض حالة نظام الفحص والجدولة"""
    await call.message.answer("📊 **نظام الجدولة الذاتي مفعّل ويعمل في الخلفية لمراقبة المنشورات القادمة.**")
    await call.answer()

@dp.callback_query(lambda call: call.data == "cancel_creation")
@dp.callback_query(lambda call: call.data == "back_to_main")
async def cancel_and_return(call: types.CallbackQuery, state: FSMContext):
    """إلغاء العمليات الحالية والعودة للقائمة الرئيسية"""
    await state.clear()
    await call.message.edit_text(text="🤖 لوحة التحكم الرئيسية لـ ControllerBot مفعّلة وجاهزة لخدمتك:", reply_markup=get_main_menu())
    await call.answer()

# --- ⏱️ محرك الجدولة التلقائي بالخلفية ---

async def check_and_publish_pending_posts():
    """فحص قاعدة البيانات كل 60 ثانية وإطلاق المنشورات المستحقة تلقائياً"""
    pending_posts = db_manager.get_pending_posts()
    for post in pending_posts:
        db_post_id, target_channel, text_to_publish = post
        try:
            await bot.send_message(chat_id=target_channel, text=text_to_publish, parse_mode="Markdown")
            db_manager.mark_post_as_published(db_post_id)
        except Exception:
            pass

async def main():
    post_scheduler.add_job(check_and_publish_pending_posts, 'interval', seconds=60)
    post_scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
