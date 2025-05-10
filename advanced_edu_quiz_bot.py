import os
import random
from telegram import Update, Poll
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# تخزين حالة كل مستخدم
user_state = {}

# أسئلة تجريبية
def generate_questions(count=5):
    base_questions = [
        {
            "en": "Which protocol automatically assigns IP addresses?",
            "ar": "أي بروتوكول يوزع عناوين IP تلقائيًا؟",
            "options": ["DNS", "FTP", "DHCP", "SMTP"],
            "correct": 2,
            "explanation": "DHCP dynamically assigns IP addresses to devices."
        },
        {
            "en": "Which protocol is used to translate domain names?",
            "ar": "أي بروتوكول يُستخدم لترجمة أسماء النطاقات؟",
            "options": ["FTP", "SMTP", "DNS", "HTTP"],
            "correct": 2,
            "explanation": "DNS resolves domain names to IP addresses."
        },
        {
            "en": "UDP is connectionless and faster than TCP.",
            "ar": "UDP لا يتطلب اتصال وهو أسرع من TCP.",
            "options": ["True", "False", "Depends", "n"],
            "correct": 0,
            "explanation": "UDP offers speed by skipping connection setup and reliability checks."
        }
    ]
    return random.sample(base_questions * ((count // len(base_questions)) + 1), count)

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome!\n"
        "أرسل ملف المحاضرة أو ابدأ بـ /quiz لتوليد اختبار.\n"
        "اكتب /quiz لتجربة توليد أسئلة."
    )

# أمر /quiz
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {
        "questions": generate_questions(5),
        "current": 0,
        "score": 0
    }
    await send_question(update, context)

# إرسال سؤال للمستخدم
async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_state.get(user_id)

    if not state or state["current"] >= len(state["questions"]):
        return await show_result(update, context)

    q = state["questions"][state["current"]]
    combined = list(enumerate(q["options"]))
    random.shuffle(combined)
    shuffled = [opt for _, opt in combined]
    correct_index = next(i for i, (idx, _) in enumerate(combined) if idx == q["correct"])

    # حفظ ترتيب الاختيارات والصح
    state["questions"][state["current"]]["shuffled"] = shuffled
    state["questions"][state["current"]]["correct_index"] = correct_index

    question_text = f"{q['en']}\n{q['ar']}"

    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=question_text,
        options=shuffled,
        type=Poll.QUIZ,
        correct_option_id=correct_index,
        explanation=q["explanation"],
        is_anonymous=False
    )

# التعامل مع poll
async def handle_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_state.get(user_id)

    if not state:
        return

    question_index = state["current"]
    correct_index = state["questions"][question_index].get("correct_index", -1)

    if update.poll.correct_option_id == correct_index:
        state["score"] += 1

    state["current"] += 1
    await send_question(update, context)

# إظهار النتيجة
async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = user_state.get(update.effective_user.id)
    score = state["score"]
    total = len(state["questions"])
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"اختبارك انتهى!\nنتيجتك: {score}/{total} بنسبة {(score/total)*100:.0f}%"
    )

# تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("quiz", quiz))
app.add_handler(MessageHandler(filters.POLL, handle_poll))
app.run_polling()
