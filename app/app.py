from internal_functions import *

log = create_logger('app.log', 'app', 10)
token = os.environ.get('token')
commands = ['/category', '/total', '/set_category']


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global commands
    log.debug(f'chat_id: {update.effective_chat.id}, user_id {update.effective_user.id}')
    commands = "\n".join(commands)
    await update.message.reply_text(f'Добро пожаловать в тестовый бот. Список команд: \n{commands}')
    await get_user_db_id(update, context)
    await create_daily_job(update, context)


@checking()
async def get_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('user_db_id')
    db.execute(
        "SELECT users_categories.id,categories.name FROM users_categories JOIN categories on categories.id = users_categories.category_id  WHERE  users_categories.user_id = %s",
        (user_id,))
    user_categories = db.fetchall()
    if not user_categories:
        await update.message.reply_text("У вас нет добавленых категорий \n:( Добавьте их через команду \n/set_category")
        return
    user_categories = sorted(user_categories, key=lambda x: x[1])
    keys = [[InlineKeyboardButton(text=f"{name}", callback_data=f"category_{id}_{name}")] for id, name in
            user_categories]
    markup = InlineKeyboardMarkup(keys)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите категорию", reply_markup=markup)


@checking()
async def get_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.execute(
        "SELECT ue.amount FROM users_expenses as ue JOIN users_categories as uc ON ue.user_category_id=uc.id  WHERE  uc.user_id = %s",
        (context.user_data.get('user_db_id'),))
    exps = db.fetchall()
    if exps:
        total = sum([x[0] for x in exps])
        text = f"Общая сумма расходов составляет {total}"
    else:
        text = f"У вас пока нет расходов. Добавьте их через категории"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


@checking()
async def set_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Введите название категории")
    context.user_data['action'] = 'setting_category'


@checking()
async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = str(context.user_data.get('setting_category')).capitalize().strip()
    user_id = context.user_data.get('user_db_id')
    db.execute("SELECT id,name FROM categories WHERE  name = %s", (category,))
    cat = db.fetchone()
    if not cat:
        db.execute("INSERT INTO categories (name) VALUES (%s) RETURNING id", (category,))
        db_connection.commit()
        cat_id = db.fetchone()[0]
    else:
        cat_id = cat[0]
    db.execute("SELECT id FROM users_categories WHERE  user_id = %s and category_id = %s", (user_id, cat_id,))
    if db.fetchone():
        text = f'Категория \"{category}\" у вас уже есть'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        return
    db.execute("INSERT INTO users_categories (user_id,category_id) VALUES (%s,%s)", (user_id, cat_id,))
    db_connection.commit()
    text = f'Категория \"{category}\" успешно добавлена'
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    context.user_data['action'] = 0


async def enter_date_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Сегодня", callback_data=f"date_today")],
        [InlineKeyboardButton(text="Вчера", callback_data=f"date_yestarday")],
        [InlineKeyboardButton(text="Позавчера", callback_data=f"date_preyestarday")],
        [InlineKeyboardButton(text="Ввести вручную", callback_data=f"date_write")],
        [InlineKeyboardButton(text="Назад", callback_data=f"date_back")]
    ])
    text = f"Категория {context.user_data.get('choosen_category_name')}, выберете дату"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=markup)


async def write_date_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"Введите дату в формате ДД.ММ.ГГ"
    markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Назад", callback_data=f"add_expenses_back")]])
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=markup)


async def write_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date = str(context.user_data.get('writed_date')).replace(',', '.').replace(' ', '.')
    log.debug(f'date: {date}')
    try:
        date = datetime.datetime.strptime(date, '%d.%m.%y').date()
    except:
        text = "Ошибка! Дата введена некорректно. Исправьте и отправьте сообщение повторно."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        return
    context.user_data['expenses_date'] = date
    await show_expenses(update, context)


async def delete_expenses_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Выберете пункты для удаления"
    date = context.user_data.get('expenses_date')
    cat_id = context.user_data.get('choosen_category_id')
    db.execute("SELECT id,name,amount FROM users_expenses  WHERE  user_category_id = %s and date = %s", (cat_id, date,))
    exps = db.fetchall()
    log.debug(f'date: {date}, cat_id: {cat_id}')
    markup = []
    for id, name, amount in exps:
        caption = f"{name} - {amount if int(amount) != amount else int(amount)}"
        markup.append([InlineKeyboardButton(text=caption, callback_data=f"del_exp_{id}")])
    markup.append([InlineKeyboardButton(text="Назад", callback_data=f"add_expenses_back")])
    markup = InlineKeyboardMarkup(markup)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=markup)


async def add_expenses_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Введите название траты и сумму через пробел (можно несколько строк)"
    markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Назад", callback_data=f"write_expenses_back")]])
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=markup)


async def add_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exps = str(context.user_data.get('writed_expenses')).split('\n')
    for exp in exps:
        if ' ' in exp:
            name, amount = exp[:exp.rindex(' ')], exp[exp.rindex(' ') + 1:]
            try:
                amount = float(amount.replace(',', '.'))
            except:
                text = "Ошибка! Сумма введена некорректно. Исправьте и отправьте сообщение повторно."
                await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
                return
            db.execute("INSERT INTO users_expenses (name,amount,user_category_id,date) VALUES (%s, %s, %s, %s)",
                       (name, amount, context.user_data['choosen_category_id'], context.user_data['expenses_date'],))
            db_connection.commit()
        else:
            text = "Ошибка! Данные введены некорректно. Исправьте и отправьте сообщение повторно."
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            return
    context.user_data['action'] = 'show_expenses'
    await show_expenses(update, context)


@checking()
async def show_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date = context.user_data.get('expenses_date')
    user_id = context.user_data.get('user_db_id')
    cat_id = context.user_data.get('choosen_category_id')
    markup = [[InlineKeyboardButton(text="Добавить", callback_data=f"add_expenses")]]
    text = f"Категория {context.user_data.get('choosen_category_name')}, дата {date.strftime('%d.%m.%Y')}"
    db.execute("SELECT name,amount FROM users_expenses  WHERE  user_category_id = %s and date = %s", (cat_id, date,))
    exps = db.fetchall()
    log.debug(f'date: {date}, cat_id: {cat_id}')
    if exps:
        text += '\n' + '\n'.join(
            [f"{name} - {amount if int(amount) != amount else int(amount)}" for name, amount in exps])
        markup.append([InlineKeyboardButton(text="Удалить", callback_data=f"del_expenses")])
    else:
        text += "\nСписок пуст!"
    markup.append([InlineKeyboardButton(text="Назад", callback_data=f"add_expenses_back")])
    markup = InlineKeyboardMarkup(markup)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=markup)


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith('tz_'):
        timezone = query.data[3:]
        await set_user_tz(update, context, timezone)
    elif query.data.startswith('category_'):
        category = query.data[9:]
        context.user_data['action'] = 'choose_date'
        context.user_data['choosen_category_id'] = category[:category.index('_')]
        context.user_data['choosen_category_name'] = category[category.index('_') + 1:]
        await enter_date_caption(update, context)
    elif query.data == 'date_back':
        context.user_data['action'] = 'choose_category'
        context.user_data['choosen_category_id'] = 0
        context.user_data['choosen_category_name'] = 0
        await get_categories(update, context)
    elif query.data == 'date_write':
        context.user_data['action'] = 'write_date'
        await write_date_caption(update, context)
    elif query.data.startswith('date_'):
        day = {'today': 0, 'yestarday': 1, 'preyestarday': 2}[query.data[5:]]
        tz = await get_user_tz(update, context)
        date = datetime.datetime.now(tz=pytz.timezone(tz)) - datetime.timedelta(days=day)
        context.user_data['expenses_date'] = date.date()
        await show_expenses(update, context)
    elif query.data == 'add_expenses_back':
        context.user_data['action'] = 'choose_date'
        await enter_date_caption(update, context)
    elif query.data == 'add_expenses':
        context.user_data['action'] = 'write_expenses'
        await add_expenses_caption(update, context)
    elif query.data == 'write_expenses_back':
        context.user_data['action'] = 'show_expenses'
        await show_expenses(update, context)
    elif query.data == 'del_expenses':
        context.user_data['action'] = 'delete_expenses'
        await delete_expenses_caption(update, context)
    elif query.data.startswith('del_exp_'):
        exp_id = query.data[8:]
        db.execute("DELETE FROM users_expenses WHERE id = %s", (exp_id,))
        await delete_expenses_caption(update, context)


async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # log.debug(f'message: {update.message}')
    msg = update.message.text
    if msg.startswith('/'):
        await update.effective_message.reply_text("Такой команды не существует :(")
        return
    log.debug(f'message: {msg}, action: {context.user_data.get("action", 0)}')
    if context.user_data.get('action') == 'setting_category':
        context.user_data['setting_category'] = msg
        await add_category(update, context)
    elif context.user_data.get('action') == 'write_expenses':
        context.user_data['writed_expenses'] = msg
        await add_expenses(update, context)
    elif context.user_data.get('action') == 'write_date':
        context.user_data['writed_date'] = msg
        await write_date(update, context)


async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Такой команды не существует :(")


if __name__ == "__main__":
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(buttons))
    application.add_handler(CommandHandler('category', get_categories))
    application.add_handler(CommandHandler('total', get_total))
    application.add_handler(CommandHandler('set_category', set_category))
    application.add_handler(MessageHandler(filters.TEXT, messages))
    # application.add_handler(MessageHandler(filters.COMMAND, unknown_cmd))

    application.run_polling()

# python-telegram-bot
# python-dotenv
# psycopg2
# python-telegram-bot[job_queue]
