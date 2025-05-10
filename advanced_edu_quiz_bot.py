
import os
import random
from telegram import Update, Poll, InputFile, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# متغيرات مؤقتة
user_state = {}

# توليد سؤال وهمي (بدلاً من تحليل ملف حقيقي الآن)
def generate_questions(count=5, difficulty="easy"):
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
            "ar": "بروتوكول UDP أسرع وغير موثوق مثل TCP.",
            "options": ["True", "False", "Depends", "n"],
            "correct": 0,
            "explanation": "UDP offers speed by skipping connection setup and reliability checks."
        }
    ]
    return random.sample(base_questions * (count // len(base_questions) + 1), count)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
 await update.message.reply_text(
    """Welcome!
أرسل ملف المحاضرة أو ابدأ بـ /quiz لتوليد اختبار.
اكتب /quiz لتجربة توليد أسئلة."""
)


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {
        "questions": generate_questions(5),
        "current": 0,
        "score": 0
    }
    await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_state.get(user_id)
    if not state or state["current"] >= len(state["questions"]):
        return await show_result(update, context)

    q = state["questions"][state["current"]]
    combined_options = list(enumerate(q["options"]))
    random.shuffle(combined_options)
    shuffled_options = [opt for i, opt in combined_options]
    correct_index = [i for i, (idx, _) in enumerate(combined_options) if idx == q["correct"]][0]

    state["questions"][state["current"]]["shuffled"] = shuffled_options
    state["questions"][state["current"]]["correct_index"] = correct_index

    question_text = f"{q['en']}\n{q['ar']}"

    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=question_text,
        options=shuffled_options,
        type=Poll.QUIZ,
        correct_option_id=correct_index,
        explanation=q["explanation"],
        is_anonymous=False
    )

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

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = user_state.get(update.effective_user.id)
    score = state["score"]
    total = len(state["questions"])
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"✅ اختبارك انتهى!"
📊 نتيجتك: {score}/{total} ({(score/total)*100:.0f}%)"
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("quiz", quiz))
app.add_handler(MessageHandler(filters.POLL, handle_poll))
app.run_polling()
