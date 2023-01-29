from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler, JobQueue
from dotenv import load_dotenv, find_dotenv
from pytz import country_timezones
import datetime, logging, os, psycopg2, functools, pytz

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(module)s | %(message)s", level=logging.INFO,
                    datefmt='%d.%m.%y %H:%M:%S')
log = logging.getLogger(__name__)
load_dotenv(find_dotenv())
db_connection = psycopg2.connect(
    database=os.environ.get('database_name'),
    user=os.environ.get('database_user'),
    password=os.environ.get('database_password'),
    host=os.environ.get('database_url'),
    port=os.environ.get('database_port')
)
db = db_connection.cursor()


async def get_user_db_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_db_id = context.user_data.get('user_db_id', 0)
    if not user_db_id:
        db.execute("SELECT telegram_id FROM users WHERE  telegram_id = %s", (update.effective_user.id,))
        user_db_id = db.fetchone()
        user_db_id = user_db_id[0] if user_db_id else 0
        context.user_data['user_db_id'] = user_db_id
    if not user_db_id:
        first_name = update.effective_user.first_name if update.effective_user.first_name else ''
        last_name = update.effective_user.last_name if update.effective_user.last_name else ''
        username = update.effective_user.username if update.effective_user.username else ''
        try:
            db.execute("INSERT INTO users (telegram_id,first_name,last_name,username) VALUES (%s, %s, %s, %s)",
                       (update.effective_user.id, first_name, last_name, username,))
            db_connection.commit()
            user_db_id = await get_user_db_id(update, context)
        except:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Не могу вас добавить :(")
    return user_db_id


async def get_user_tz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_tz = context.user_data.get('user_tz', 0)
    if not user_tz:
        db.execute("SELECT timezone FROM users WHERE  telegram_id = %s", (update.effective_user.id,))
        user_tz = db.fetchone()
        user_tz = user_tz[0] if user_tz and user_tz[0] else 0
        context.user_data['user_tz'] = user_tz
    if not user_tz:
        region = str(update.effective_user.language_code)
        timezones = country_timezones(region)
        keys = [[InlineKeyboardButton(text=f"{x}", callback_data=f"tz_{x}")] for x in timezones]
        reply_markup = InlineKeyboardMarkup(keys)
        text = "Для работы службы ежедневного оповещения о тратах, выберете ваш часовой пояс:"
        await update.message.reply_text(text, reply_markup=reply_markup)
    return user_tz


async def set_user_tz(update: Update, context: ContextTypes.DEFAULT_TYPE, tz):
    db.execute("UPDATE users SET timezone = %s WHERE telegram_id = %s", (tz, update.effective_user.id,))
    db_connection.commit()
    await get_user_tz(update, context)
    now = datetime.datetime.now(tz=pytz.timezone(tz))
    wd = {0: 'Воскресенье', 1: 'Понедельник', 2: 'Вторник', 3: 'Среда', 4: 'Четверг', 5: 'Пятница', 6: 'Суббота'}
    cur = now.strftime('%d.%m.%Y') + f', {wd[int(now.strftime("%w"))]}, ' + now.strftime('%H:%M:%S')
    text = f'Вы выбрали часовой пояс {tz}, текущие дата и время:  {cur}'
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    await create_daily_job(update, context)


async def create_daily_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id, user_id = update.effective_chat.id, update.effective_user.id
    job_name = f'{user_id}_{chat_id}_{daily_sum}'
    job_exist = context.job_queue.get_jobs_by_name(job_name)
    tz = await get_user_tz(update, context)
    if job_exist or not tz:
        return
    exec_time = datetime.time(hour=23, minute=59, tzinfo=pytz.timezone(tz))
    context.job_queue.run_daily(daily_sum, exec_time, chat_id=chat_id, name=job_name, user_id=user_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Ежедневная задача создана.")


async def daily_sum(context: ContextTypes.DEFAULT_TYPE):
    tz = context.user_data.get('user_tz', 0)
    date = datetime.datetime.now(tz=pytz.timezone(tz)).date()
    db.execute(
        "SELECT ue.amount,c.name FROM users_expenses as ue JOIN users_categories as uc ON ue.user_category_id=uc.id JOIN categories as c ON c.id=uc.category_id  WHERE  uc.user_id = %s and ue.date = %s",
        (context.user_data.get('user_db_id'), date,))
    exps = db.fetchall()
    if exps:
        exps_total = {}
        total = 0
        for amount, name in exps:
            if name in exps_total:
                exps_total[name] = exps_total[name] + amount
            else:
                exps_total.update({name: amount})
            total += amount
        text = f"{date.strftime('%Y-%m-%d')}\n"
        for name, amount in exps_total.items():
            text += f'{name}: {amount if int(amount) != amount else int(amount)}\n'
        text += f'Total: {total if int(total) != total else int(total)}'
    else:
        text = "Сегодня у вас нет расходов."
    await context.bot.send_message(chat_id=context.job.chat_id, text=text)


def checking():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args):
            await get_user_db_id(*args)
            await get_user_tz(*args)
            await create_daily_job(*args)
            args[1].user_data['action'] = 0
            return await func(*args)

        return wrapped

    return wrapper
