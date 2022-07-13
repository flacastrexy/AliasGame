import random
from random import sample
import bot_config
import database
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from users_config import user_data
import time
import asyncio

TOKEN = bot_config.BOT_TOKEN  # Bot token

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


def menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = (
        types.KeyboardButton("Новая игра ▶️"),
        types.KeyboardButton("Настройки ⚙"),
    )
    markup.add(*buttons)
    return markup


def pre_start_markup():
    markup = types.InlineKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.InlineKeyboardButton("Начать ➡️", callback_data='start'))
    buttons = (
        types.InlineKeyboardButton("Сменить названия команд 🔀", callback_data='re_team'),
        types.InlineKeyboardButton("Изменить темы 🔀", callback_data='re_theme'),
    )
    markup.add(*buttons)
    return markup


def player_count_markup():
    markup = types.InlineKeyboardMarkup(row_width=3)
    for i in range(3):
        buttons = (
            types.InlineKeyboardButton(str(i*3 + 2), callback_data='player_count_' + str(i*3 + 2)),
            types.InlineKeyboardButton(str(i*3 + 3), callback_data='player_count_' + str(i*3 + 3)),
            types.InlineKeyboardButton(str(i*3 + 4), callback_data='player_count_' + str(i*3 + 4)),
        )
        markup.add(*buttons)
    return markup


def themes_markup(user_id):
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = False
    for theme in database.themes.keys():
        if theme not in user_data[user_id]['themes']:
            lenght = len(database.themes[theme])
            markup.add(types.InlineKeyboardButton(str(theme)+" (" + str(lenght) + ")", callback_data='themes_'+str(theme)))
            buttons = True
    if buttons:
        markup.add(types.InlineKeyboardButton('Выбрать все ☠️', callback_data='themes_all'))
    markup.add(types.InlineKeyboardButton("Продолжить ✅", callback_data='themes_cont'))
    return markup


def game_markup(new_word):
    markup = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton("👍", callback_data='game_yes_' + str(new_word))
    button2 = types.InlineKeyboardButton("👎🏻", callback_data='game_no_' + str(new_word))
    markup.add(button2, button1)
    return markup


def check_score(user_id):
    for key, score in user_data[user_id]['teams'].items():
        if score >= user_data[user_id]['words_to_win']:
            return True
        else:
            return False


def get_winner_team(user_id):
    for key, score in user_data[user_id]['teams'].items():
        if score >= user_data[user_id]['words_to_win']:
            return str(key)


def round_statistic(user_id):
    text = "Статистика раунда 📈:\n"
    plus_score = 0
    for word in user_data[user_id]['words_last_round']:
        if user_data[user_id]['words_last_round'][word] == 1:
            text += str(word) + "✅\n"
            plus_score += 1
        else:
            text += str(word) + "❌\n"
    text += "------------------------\n"
    text += "Текущие очки:\n"
    current_walk = user_data[user_id]['current_move']
    team_name = user_data[user_id]['teams_name'][current_walk]
    for key, score in user_data[user_id]['teams'].items():
        if key == team_name:
            text += "👉" + str(key) + ": " + str(score) + " (+" + str(plus_score) + ")\n"
        else:
            text += "👉" + str(key) + ": " + str(score) + "\n"
    if user_data[user_id]['current_move'] >= len(user_data[user_id]['teams'])-1:
        user_data[user_id]['current_move'] = 0
    else:
        user_data[user_id]['current_move'] += 1
    current_walk = user_data[user_id]['current_move']
    team_name = user_data[user_id]['teams_name'][current_walk]
    text += 'Команда ' + '<b>' + str(team_name) + "</b>" + " готовтесь"
    return text


def next_round_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Готов ✅", callback_data='ready'))
    return markup


def default_user_data():
    return {
        'teams': {

        },
        'themes': [],
        'teams_name': [],
        'old_words': [],
        'round_time': 30,
        'words_to_win': 30,
        'fine': False,  # штраф за пропуск
        'current_move': 0,
        'all_words': [],
        'words_last_round': {},
        'end_time': False,
        'step': 'menu',
        'local_time': 0,
    }


def rework_words(user_id):
    user_data[user_id]['old_words'] = []


def get_simple_settings(user_id):
    round_time = user_data[user_id]['round_time']
    words_to_win = user_data[user_id]['words_to_win']
    fine = ""
    if user_data[user_id]['fine']:
        fine = "Да"
    else:
        fine = "Нет"
    text = "\n<b>Время раунда</b>⏳: " + str(round_time) + "\n<b>Количество слов до победы</b>🧠: " + str(words_to_win)\
           + "\n<b>Штрафы за пропуск:</b> " + str(fine)
    return text


def settings_time_markup():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = (
        types.InlineKeyboardButton("30", callback_data='settime_30'),
        types.InlineKeyboardButton("60", callback_data='settime_60'),
        types.InlineKeyboardButton("90", callback_data='settime_90'),
        types.InlineKeyboardButton("120", callback_data='settime_120'),
        types.InlineKeyboardButton("150", callback_data='settime_150'),
        types.InlineKeyboardButton("180", callback_data='settime_180'),
        types.InlineKeyboardButton("240", callback_data='settime_240'),
        types.InlineKeyboardButton("300", callback_data='settime_300'),
    )
    markup.add(*buttons)
    return markup


def settings_words_markup():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = (
        types.InlineKeyboardButton("10", callback_data='setwords_10'),
        types.InlineKeyboardButton("15", callback_data='setwords_15'),
        types.InlineKeyboardButton("20", callback_data='setwords_20'),
        types.InlineKeyboardButton("25", callback_data='setwords_25'),
        types.InlineKeyboardButton("30", callback_data='setwords_30'),
        types.InlineKeyboardButton("40", callback_data='setwords_40'),
        types.InlineKeyboardButton("60", callback_data='setwords_60'),
        types.InlineKeyboardButton("100", callback_data='setwords_100'),
    )
    markup.add(*buttons)
    return markup


def settings_fine_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = (
        types.InlineKeyboardButton("Да", callback_data='setfine_yes'),
        types.InlineKeyboardButton("Нет", callback_data='setfine_no')
    )
    markup.add(*buttons)
    return markup


def settings_refresh_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = (
        types.InlineKeyboardButton("Да", callback_data='setrefresh_yes'),
        types.InlineKeyboardButton("Нет", callback_data='setrefresh_no')
    )
    markup.add(*buttons)
    return markup


def settings_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton("Время раунда", callback_data='settings_time')
    button2 = types.InlineKeyboardButton("Кол-во слов", callback_data='settings_words')
    button3 = types.InlineKeyboardButton("Штрафы за пропуск", callback_data='settings_fine')
    button4 = types.InlineKeyboardButton("Сбросить слова", callback_data='settings_refresh')
    markup.add(button1, button2)
    markup.add(button3, button4)
    return markup


def get_player_settings(user_id):
    teams = "\n👉".join(user_data[user_id]['teams'])
    round_time = user_data[user_id]['round_time']
    words_to_win = user_data[user_id]['words_to_win']
    fine = ''
    if user_data[user_id]['fine']:
        fine = 'Да'
    else:
        fine = 'Нет'
    themes = ", ".join(user_data[user_id]['themes'])
    text = '<b>Команды</b>🤝: \n👉' + teams + "\n<b>Темы</b>🗣: " + themes + "\n<b>Время раунда</b>⏳: " \
           + str(round_time) + "\n<b>Количество слов до победы</b>🧠: " + str(words_to_win) +\
           "\n<b>Штрафы за пропуск:</b> " + str(fine) + "\nПосетите меню '<b>Настройки</b>', чтобы изменить их!"
    return text


def end_game(user_id):
    for team in user_data[user_id]['teams']:
        user_data[user_id]['teams'][team] = 0
    user_data[user_id]['themes'] = []
    user_data[user_id]['teams_name'] = []
    user_data[user_id]['current_move'] = []
    user_data[user_id]['all_words'] = []
    user_data[user_id]['words_last_round'] = {}
    user_data[user_id]['step'] = 'menu'
    user_data[user_id]['end_time'] = False


def get_new_word(user_id):
    random.shuffle(user_data[user_id]['all_words'])
    for word in user_data[user_id]['all_words']:
        if word not in user_data[user_id]['old_words']:
            user_data[user_id]['old_words'].append(word)
            user_data[user_id]['words_last_round'][str(word)] = 0
            return word


def is_have_new_word(user_id):
    for word in user_data[user_id]['all_words']:
        if word not in user_data[user_id]['old_words']:
            return True
    return False


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    photo = types.InputFile("img/Alias_logo.png")
    await bot.send_photo(chat_id=message.chat.id, photo=photo)
    await message.answer("Добро пожаловать в бот для игры в <b>Alias</b> 😁", parse_mode='html',
                         reply_markup=menu_markup())


@dp.message_handler(content_types=['text'])
async def start(message: types.Message):
    if message.chat.type == 'private':
        if message.text == "Новая игра ▶️":
            if message.from_user.id not in user_data:
                user_data[message.from_user.id] = default_user_data()
            if user_data[message.from_user.id]['step'] == 'game' or user_data[message.from_user.id]['step'] == 'round':
                markup = types.InlineKeyboardMarkup(row_width=2)
                button1 = types.InlineKeyboardButton("Да", callback_data='newgame_yes')
                button2 = types.InlineKeyboardButton("Нет", callback_data='newgame_no')
                markup.add(button1, button2)
                await message.answer("Кажется, вы уже находитесь в игре, хотите начать новую?", reply_markup=markup)
            else:
                end_game(message.from_user.id)
                await message.answer("Выберите количество команд (игроков) 😏", reply_markup=player_count_markup())
        elif message.text == "Настройки ⚙":
            if message.from_user.id not in user_data:
                user_data[message.from_user.id] = default_user_data()
            await message.answer("Текущие настройки:\n" + get_simple_settings(message.from_user.id),
                                 reply_markup=settings_markup(), parse_mode='html')


@dp.callback_query_handler(Text(startswith="newgame_"))
async def callback_inline(call: types.CallbackQuery):
    if call.from_user.id in user_data:
        callback = call.data.split("_")[1]
        if callback == 'yes':
            end_game(call.from_user.id)
            await call.message.answer("Выберите количество команд (игроков) 😏", reply_markup=player_count_markup())
            await call.message.delete()
            await call.answer()
        if callback == 'no':
            await call.message.delete()
            await call.answer()

    else:
        await bot.send_message(call.message.chat.id,
                               "Кажется, вы новый пользователь. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
        await call.answer()


@dp.callback_query_handler(Text(startswith="settings_"))
async def callback_inline(call: types.CallbackQuery):
    if call.from_user.id in user_data:
        setting = call.data.split("_")[1]
        if setting == 'time':
            await bot.send_message(call.message.chat.id, "Выберите новое <b>Время раунда</b>⏳ : ", parse_mode='html',
                                   reply_markup=settings_time_markup())
            await call.answer()
        if setting == 'words':
            await bot.send_message(call.message.chat.id, "Выберите новое <b>Количество слов до победы</b>🧠: ", parse_mode='html',
                                   reply_markup=settings_words_markup())
            await call.answer()
        if setting == 'fine':
            await bot.send_message(call.message.chat.id, "Выберите новое правило: <b>Штрафы за пропуск</b> ", parse_mode='html',
                                   reply_markup=settings_fine_markup())
            await call.answer()
        if setting == 'refresh':
            await bot.send_message(call.message.chat.id, "Вы действительно хотите сбросить слова?\n(Слова, которые вам уже попадались будут попадаться снова)",
                                   parse_mode='html',
                                   reply_markup=settings_refresh_markup())
            await call.answer()
    else:
        await bot.send_message(call.message.chat.id,
                               "Кажется, вы новый пользователь. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
        await call.answer()


@dp.callback_query_handler(Text(startswith="settime_"))
async def callback_inline(call: types.CallbackQuery):
    if call.from_user.id in user_data:
        setting = call.data.split("_")[1]
        user_data[call.from_user.id]['round_time'] = int(setting)
        await bot.send_message(call.message.chat.id,
                               "Настройки успешно изменены!\n" + get_simple_settings(call.from_user.id), reply_markup=menu_markup(), parse_mode='html')
        await call.answer()
    else:
        await bot.send_message(call.message.chat.id,
                               "Кажется, вы новый пользователь. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
        await call.answer()


@dp.callback_query_handler(Text(startswith="setwords_"))
async def callback_inline(call: types.CallbackQuery):
    if call.from_user.id in user_data:
        setting = call.data.split("_")[1]
        user_data[call.from_user.id]['words_to_win'] = int(setting)
        await bot.send_message(call.message.chat.id,
                               "Настройки успешно изменены!\n" + get_simple_settings(call.from_user.id),
                               reply_markup=menu_markup(), parse_mode='html')
        await call.answer()
    else:
        await bot.send_message(call.message.chat.id,
                               "Кажется, вы новый пользователь. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
        await call.answer()


@dp.callback_query_handler(Text(startswith="setfine_"))
async def callback_inline(call: types.CallbackQuery):
    if call.from_user.id in user_data:
        setting = call.data.split("_")[1]
        if setting == "yes":
            user_data[call.from_user.id]['fine'] = True
        if setting == "no":
            user_data[call.from_user.id]['fine'] = False
        await bot.send_message(call.message.chat.id,
                               "Настройки успешно изменены!\n" + get_simple_settings(call.from_user.id),
                               reply_markup=menu_markup(), parse_mode='html')
        await call.answer()
    else:
        await bot.send_message(call.message.chat.id,
                               "Кажется, вы новый пользователь. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
        await call.answer()


@dp.callback_query_handler(Text(startswith="setrefresh_"))
async def callback_inline(call: types.CallbackQuery):
    if call.from_user.id in user_data:
        setting = call.data.split("_")[1]
        if setting == "yes":
            rework_words(call.from_user.id)
            await bot.send_message(call.message.chat.id,
                                   "Словарь сброшен!\n" + get_simple_settings(call.from_user.id),
                                   reply_markup=menu_markup(), parse_mode='html')
            await call.answer()
        if setting == "no":
            await bot.send_message(call.message.chat.id,
                                   "Словарь в целлости и сохранности!\n" + get_simple_settings(call.from_user.id),
                                   reply_markup=menu_markup(), parse_mode='html')
            await call.answer()
    else:
        await bot.send_message(call.message.chat.id,
                               "Кажется, вы новый пользователь. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
        await call.answer()


@dp.callback_query_handler(Text(startswith="player_count_"))
async def callback_inline(call: types.CallbackQuery):
    if call.from_user.id in user_data:
        players_count = call.data.split("_")[2]
        user_data[call.from_user.id]['teams'].clear()
        random_teams = sample(database.default_teams, int(players_count))
        for i in random_teams:
            user_data[call.from_user.id]['teams'][str(i)] = 0
        await bot.send_message(call.message.chat.id, "Выберите темы🧠:", parse_mode='html',
                               reply_markup=themes_markup(call.from_user.id))
        await call.answer()
    else:
        await bot.send_message(call.message.chat.id,
                               "Кажется, вы новый пользователь. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
        await call.answer()


@dp.callback_query_handler(Text(startswith="themes_"))
async def callback_inline(call: types.CallbackQuery):
    if call.from_user.id in user_data:
        if user_data[call.from_user.id]['step'] == 'menu' or user_data[call.from_user.id]['step'] == 'pre_start':
            theme_callback = call.data.split("_")[1]
            if theme_callback == 'all':
                user_data[call.from_user.id]['themes'].clear()
                for theme in database.themes:
                    user_data[call.from_user.id]['themes'].append(theme)
                await bot.send_message(call.message.chat.id,
                                       "Выбраные темы:\n👉" + "\n👉".join(user_data[call.from_user.id]['themes']),
                                       reply_markup=themes_markup(call.from_user.id))
                await call.answer()
            elif theme_callback == 'cont':
                if not user_data[call.from_user.id]['themes']:
                    await bot.send_message(call.message.chat.id, "Ваш список тем пуст 🤔\nВыберите темы🧠:", reply_markup=themes_markup(call.from_user.id))
                    await call.answer()
                else:
                    await bot.send_message(call.message.chat.id, get_player_settings(call.from_user.id), parse_mode='html', reply_markup=pre_start_markup())
                    user_data[call.from_user.id]['step'] = 'pre_start'
                    await call.answer()
            else:
                if theme_callback not in user_data[call.from_user.id]['themes']:
                    user_data[call.from_user.id]['themes'].append(theme_callback)
                await bot.send_message(call.message.chat.id, "Выбраные темы:\n👉" + "\n👉".join(user_data[call.from_user.id]['themes']),
                                       reply_markup=themes_markup(call.from_user.id))
                await call.answer()
        else:
            await bot.send_message(call.message.chat.id,
                               "Кажется, вы уже в игре или еще не начали новую. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())

    else:
        await bot.send_message(call.message.chat.id,
                               "Кажется, вы новый пользователь. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
        await call.answer()


@dp.callback_query_handler(Text(startswith="re_"))
async def callback_inline(call: types.CallbackQuery):
    if call.from_user.id in user_data:
        if user_data[call.from_user.id]['step'] == 'pre_start':
            re_callback = call.data.split("_")[1]
            if re_callback == 'team':
                players_count = len(user_data[call.from_user.id]['teams'])
                user_data[call.from_user.id]['teams'].clear()
                random_teams = sample(database.default_teams, int(players_count))
                for i in random_teams:
                    user_data[call.from_user.id]['teams'][str(i)] = 0
                await bot.send_message(call.message.chat.id, get_player_settings(call.from_user.id), parse_mode='html',
                                           reply_markup=pre_start_markup())
                await call.answer()
            if re_callback == 'theme':
                user_data[call.from_user.id]['themes'].clear()
                await bot.send_message(call.message.chat.id, "Выберите темы🧠:",
                                       reply_markup=themes_markup(call.from_user.id))
        else:
            await bot.send_message(call.message.chat.id,
                               "Кажется, вы не выбрали новое количество игроков или уже находитесь в игре🤥. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())

    else:
        await bot.send_message(call.message.chat.id,
                               "Кажется, вы новый пользователь. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
        await call.answer()


@dp.callback_query_handler(lambda c: c.data == 'start')
async def callback_inline(call: types.CallbackQuery):
    if call.from_user.id in user_data:
        if user_data[call.from_user.id]['step'] == 'pre_start':
            user_data[call.from_user.id]['step'] = 'game'
            await call.message.edit_reply_markup(None)
            user_data[call.from_user.id]['teams_name'].clear()
            for team in user_data[call.from_user.id]['teams']:
                user_data[call.from_user.id]['teams_name'].append(team)
            current_walk = user_data[call.from_user.id]['current_move'] = 0
            team_name = user_data[call.from_user.id]['teams_name'][current_walk]
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Готов ✅", callback_data='ready'))
            for theme in user_data[call.from_user.id]['themes']:
                user_data[call.from_user.id]['all_words'] += database.themes[theme]
            await bot.send_message(call.message.chat.id, "Игра начинается! Команда " + "<b>" + team_name + "</b>" + " приготовтесь!", parse_mode='html', reply_markup=markup)
            await call.answer()
        else:
            await bot.send_message(call.message.chat.id,
                               "Кажется, вы не выбрали новое количество игроков или уже находитесь в игре 🤥. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())

    else:
        await bot.send_message(call.message.chat.id,
                               "Кажется, вы новый пользователь. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
        await call.answer()


@dp.callback_query_handler(lambda c: c.data == 'ready')
async def callback_inline(call: types.CallbackQuery):
    if call.from_user.id in user_data:
        try:
            if user_data[call.from_user.id]['step'] == 'round':
                await bot.send_message(call.message.chat.id, "Раунд уже идет!")
                await call.answer()
            elif user_data[call.from_user.id]['step'] == 'game':
                user_data[call.from_user.id]['step'] = 'round'
                user_data[call.from_user.id]['words_last_round'].clear()
                await call.message.edit_reply_markup(None)
                await call.answer()
                await bot.send_message(call.message.chat.id,"3...")
                time.sleep(1)
                await bot.send_message(call.message.chat.id,"2...")
                time.sleep(1)
                await bot.send_message(call.message.chat.id,"1...")
                time.sleep(1)
                timer_message = await bot.send_message(call.message.chat.id, "Время: " + str(user_data[call.from_user.id]['round_time']))
                loop = asyncio.get_event_loop()
                dp = Dispatcher(bot, loop=loop)
                dp.loop.create_task(timer(user_data[call.from_user.id]['round_time'], timer_message, call.from_user.id))
                if is_have_new_word(call.from_user.id):
                    new_word = get_new_word(call.from_user.id)
                    await bot.send_message(call.message.chat.id, new_word, reply_markup=game_markup(new_word))
                else:
                    await bot.send_message(call.message.chat.id, "Не могу найти слова :c, перезапускаю игру и словарь", reply_markup=menu_markup())
                    end_game(call.message.chat.id)
                    rework_words(call.message.chat.id)
                    await call.answer()
            else:
                await bot.send_message(call.message.chat.id,
                               "Кажется, игра уже закончилась или еще не началась 🤒. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
                await call.answer()
        except():
            print("ready не сработала")
    else:
        await bot.send_message(call.message.chat.id,
                               "Кажется, вы новый пользователь. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
        await call.answer()


@dp.callback_query_handler(Text(startswith="game_"))
async def callback_inline(call: types.CallbackQuery):
    if call.from_user.id in user_data:
        try:
            if user_data[call.from_user.id]['step'] == "round":
                re_callback = call.data.split("_")[1]
                current_word = call.data.split("_")[2]
                if re_callback == 'yes':
                    team_num = user_data[call.from_user.id]['current_move']
                    team_name = user_data[call.from_user.id]['teams_name'][team_num]
                    user_data[call.from_user.id]['teams'][team_name] += 1
                    user_data[call.from_user.id]['words_last_round'][str(current_word)] = 1
                    try:
                        if not user_data[call.from_user.id]['end_time']:
                            if is_have_new_word(call.from_user.id):
                                new_word = get_new_word(call.from_user.id)
                                await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                        text=new_word, reply_markup=game_markup(new_word))
                                await call.answer()
                            else:
                                await bot.send_message(call.message.chat.id,
                                                       "Не могу найти слова :c, перезапускаю игру и словарь",
                                                       )
                                end_game(call.message.chat.id)
                                rework_words(call.message.chat.id)
                                await call.answer()
                        else:
                            await bot.send_message(call.message.chat.id, round_statistic(call.from_user.id), parse_mode='html', reply_markup=next_round_markup())
                            user_data[call.from_user.id]['end_time'] = False
                            user_data[call.from_user.id]['step'] = 'game'
                            if check_score(call.from_user.id):
                                await bot.send_message(call.message.chat.id, "Игра окончена, победили " + get_winner_team(call.from_user.id) + " 👏🏻", parse_mode='html')
                                end_game(call.from_user.id)
                    except():
                        await bot.send_message(call.message.chat.id, "Не могу найти слова :c, перезапускаю игру и словарь",
                                              )
                        end_game(call.message.chat.id)
                        rework_words(call.message.chat.id)
                        await call.answer()
                if re_callback == 'no':
                    team_num = user_data[call.from_user.id]['current_move']
                    team_name = user_data[call.from_user.id]['teams_name'][team_num]
                    if user_data[call.from_user.id]['fine']:
                        user_data[call.from_user.id]['teams'][team_name] -= 1
                    user_data[call.from_user.id]['words_last_round'][str(current_word)] = 0
                    try:
                        if not user_data[call.from_user.id]['end_time']:
                            if is_have_new_word(call.from_user.id):
                                new_word = get_new_word(call.from_user.id)
                                await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                            text=new_word, reply_markup=game_markup(new_word))
                                await call.answer()
                            else:
                                await bot.send_message(call.message.chat.id,
                                                       "Не могу найти слова :c, перезапускаю игру и словарь",
                                                     )
                                end_game(call.message.chat.id)
                                rework_words(call.message.chat.id)
                                await call.answer()
                        else:
                            await bot.send_message(call.message.chat.id, round_statistic(call.from_user.id), parse_mode='html', reply_markup=next_round_markup())
                            user_data[call.from_user.id]['end_time'] = False
                            user_data[call.from_user.id]['step'] = 'game'
                            if check_score(call.from_user.id):
                                await bot.send_message(call.message.chat.id, "Игра окончена, победили " + get_winner_team(call.from_user.id) + " 👏🏻", parse_mode='html')
                                end_game(call.from_user.id)
                    except():
                        await bot.send_message(call.message.chat.id, "Не могу найти слова :c, перезапускаю игру и словарь",
                                              )
                        end_game(call.message.chat.id)
                        rework_words(call.message.chat.id)
                        await call.answer()
            else:
                await bot.send_message(call.message.chat.id,
                                       "Кажется, игра закончилась или еще не началась. Нажмите 'Новая игра', чтобы начать 👀",
                                       reply_markup=menu_markup())
                await call.answer()
        except():
            print("game_ не сработала")
    else:
        await bot.send_message(call.message.chat.id,
                               "Кажется, вы новый пользователь. Нажмите 'Новая игра', чтобы начать 👀",
                               reply_markup=menu_markup())
        await call.answer()


async def timer(round_time, timer_message, user_id):
    user_data[user_id]['local_time'] = round_time
    while user_data[user_id]['local_time'] > 0:
        user_data[user_id]['local_time'] -= 1
        await bot.edit_message_text(chat_id=timer_message.chat.id, message_id=timer_message.message_id,
                                    text="Время: " + str(user_data[user_id]['local_time']))
        await asyncio.sleep(1)
    await bot.edit_message_text(chat_id=timer_message.chat.id, message_id=timer_message.message_id,
                                text="Время кончилось, но вы можете отгадать последнее слово! ")
    user_data[user_id]['end_time'] = True


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp, skip_updates=True)

