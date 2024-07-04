import telebot
import json
from telebot import types
import psycopg2
import os
from parse import get_vacancies, get_resumes


# DATABASE
database = os.environ['POSTGRES_DB']
user = os.environ['POSTGRES_USER']
password = os.environ['POSTGRES_DB_PASSWORD']
conn = psycopg2.connect(database=database,
                        user=user,
                        password=password,
                        host="db",
                        port="5432", )
cursor = conn.cursor()

# CONST
SITES = ("hh.ru", "avito", "habr")
DATA_TYPES = ("вакансии", "резюме")
EXP = ("не имеет значения", "от 1 года до 3 лет", "нет опыта", "от 3 до 6 лет", "более 6 лет")
EDUCATION_V = ("не имеет значения", "не требуется или не указано", "высшее", "среднее профессиональное")
EDUCATION_R = ("не имеет значения", "среднее", "среднее специальное", "незаконченное высшее", "бакалавр", "магистр",
               "высшее", "кандидат наук", "доктор наук")
SCHEDULE = ("не имеет значения", "полный день", "сменный график", "вахтовый метод", "удаленная работа", "гибкий график")

# BOT

token = os.environ['BOT_TOKEN']
site = ""
data_type = ""
last_parsed = ""
search_id = ""
our_filter = {}
bot = telebot.TeleBot(token)
is_parsing_in_process = False

bot.set_my_commands([
    telebot.types.BotCommand("/start", "Начальная команда бота"),
    telebot.types.BotCommand("/help", "Подробное описание бота"),
    telebot.types.BotCommand("/parse", "Запрос на получение данных"),
    telebot.types.BotCommand("/search", "Просмотр полученных данных"),
    telebot.types.BotCommand("/filter", "Добавление фильтров"),
    telebot.types.BotCommand("/now_filter", "Получение атрибутов текущего списка"),
])


@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row("HH.ru", "Avito", "Habr")
    keyboard.row("Вакансии", "Резюме")
    bot.send_message(message.chat.id,
                     'Для начала выберите сайт и цель парсинга, после чего используйте команду /parse',
                     reply_markup=keyboard)


@bot.message_handler(commands=['help'])
def start_message(message):
    bot.send_message(message.chat.id, 'Основные команды:\n' +
                     '/help - получение инфромации о командах бота\n' +
                     '/filter - добавление фильтров в запрос (уровень обучения. опыт работы и тип занятости)\n' +
                     '/now_filter - получение атрибутов текущего фильтра\n' +
                     '/parse - запрос на получение данных с сайта\n' +
                     '/search - просмотр полученных данных в виде меню анкет\n\n' +
                     'Помимо команд бот принимает следующие ключевые слова:\n\n' +
                     "Основные ключевые слова:\n" +
                     "'HH.ru', 'Avito', 'Habr' - сайты, с которых будут загружаться данные\n" +
                     "'Вакансии', 'Резюме' - тип получаемых данных\n\n" +
                     "Ключевые слова для фильтрации по опыту работы:\n" +
                     "'Не имеет значения'\n'От 1 года до 3 лет'\n'Нет опыта'\n'От 3 до 6 лет'\n'Более 6 лет'\n\n" +
                     "Ключевые слова для фильтрации по образованию:\n" +
                     "'Не имеет значения'\n'Не требуется или не указано' (для вакансий)\n'Высшее'\n" +
                     "'Среднее профессиональное' (Для вакансий)\n'Среднее' (для резюме)\n" +
                     "'Среднее специальное' (для резюме)\n'Незаконченное высшее' (для резюме)\n" +
                     "'Бакалавр' (для резюме)\n'Магистр' (для резюме)\n'Кандидат наук' (для резюме)\n" +
                     "'Доктор наук' (для резюме)\n\n" +
                     "Ключевые слова для фильтрации по опыту работы:\n" +
                     "'Не имеет значения'\n'Полный день'\n'Cменный график'\n'Вахтовый метод'\n" +
                     "'Удаленная работа'\n'Гибкий график'"
                     )


@bot.message_handler(commands=['parse'])
def parse(message):
    global site
    global data_type
    global last_parsed
    global is_parsing_in_process
    if is_parsing_in_process:
        bot.send_message(message.chat.id, 'В данный момент уже происходит запрос данных')
    elif site:
        if data_type:
            is_parsing_in_process = True
            text = message.text[7:]
            cursor.execute(f'DROP TABLE IF EXISTS data_{message.chat.id}')
            bot.send_message(message.chat.id, 'Подождите немного, происходит получение данных...')
            if data_type.lower() == "вакансии":
                cursor.execute(f'CREATE TABLE data_{message.chat.id} (id SERIAL PRIMARY KEY, name VARCHAR(256),' +
                               f'link VARCHAR(1024), ' +
                               'salary VARCHAR(256) ,company VARCHAR(256), city VARCHAR(128),exp VARCHAR(128))')
                conn.commit()
                result_num, vacancies = get_vacancies(text, our_filter)
                sql = f"INSERT INTO data_{message.chat.id} (name, link, salary, company, city, exp) VALUES "
                for vacancy in vacancies:
                    sql += cursor.mogrify("(%s,%s,%s,%s,%s,%s),", vacancy).decode('utf-8')
                cursor.execute(sql[:-1])
                conn.commit()
            else:
                cursor.execute(f'CREATE TABLE data_{message.chat.id} (id SERIAL PRIMARY KEY, name VARCHAR(512), ' +
                               'link VARCHAR(1024) , age VARCHAR(128), exp VARCHAR(128), status VARCHAR(128))')
                conn.commit()
                result_num, resumes = get_resumes(text, our_filter)
                sql = f"INSERT INTO data_{message.chat.id} (name, link, age, exp, status) VALUES "
                for resume in resumes:
                    sql += cursor.mogrify("(%s,%s,%s,%s,%s),", resume).decode('utf-8')
                cursor.execute(sql[:-1])
                conn.commit()

            cursor.execute(f"SELECT count(*) FROM data_{message.chat.id};")
            conn.commit()
            count = cursor.fetchone()
            bot.send_message(message.chat.id, 'Парсинг прошел успешно\n' +
                             f'Найдено: {result_num}\nЗагружено: {count[0]}\n' +
                             'Для просмотра результата воспользуйтесь командой /search')
            last_parsed = data_type.lower()
            is_parsing_in_process = False
        else:
            bot.send_message(message.chat.id, 'Выберите цель парсинга')
    else:
        bot.send_message(message.chat.id, 'Выберите сайт')


@bot.message_handler(commands=['search'])
def search(message):
    global search_id
    if last_parsed:
        cursor.execute(f"SELECT count(*) FROM data_{message.chat.id};")
        count = cursor.fetchone()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='<--',
                                              callback_data="{\"method\":\"pagination\",\"NumberPage\":0" +
                                                            ",\"CountPage\":" + str(count[0]) + "}"),
                   types.InlineKeyboardButton(text=f'1/{count[0]}', callback_data=" "),
                   types.InlineKeyboardButton(text='-->',
                                              callback_data="{\"method\":\"pagination\",\"NumberPage\":2" +
                                                            ",\"CountPage\":" + str(count[0]) + "}"))
        cursor.execute(f"SELECT * FROM data_{message.chat.id} WHERE id=1;")
        if data_type.lower() == "вакансии":
            our_id, name, link, salary, company, city, exp = cursor.fetchone()
            mes = bot.send_message(message.chat.id, f"{name}\n[Ссылка]({link})\n" +
                                   f"Зарплата: {salary}\nОпыт работы: {exp}\nКомпания: {company}\nГород: {city}",
                                   reply_markup=markup, parse_mode='Markdown')
            search_id = mes.message_id
        elif data_type.lower() == "резюме":
            our_id, name, link, age, experience, status = cursor.fetchone()
            mes = bot.send_message(message.chat.id, f"{name}\n[Ссылка]({link})\n" +
                                   f"Возраст: {age}\nСтаж работы: {experience}\n{status}",
                                   reply_markup=markup, parse_mode='Markdown')
            search_id = mes.message_id
    else:
        bot.send_message(message.chat.id, "Для начала используйте /parse")


@bot.message_handler(commands=['filter'])
def filter_command(message):
    global data_type
    global our_filter
    our_filter = {}
    if data_type.lower():
        keyboard = types.ReplyKeyboardMarkup()
        keyboard.row("Не имеет значения")
        keyboard.row("Нет опыта")
        keyboard.row("От 1 года до 3 лет")
        keyboard.row("От 3 до 6 лет")
        keyboard.row("Более 6 лет")
        bot.send_message(message.chat.id,
                         'Выберите необходимый опыт работы',
                         reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Для начала выберите цель парсинга')


@bot.message_handler(commands=['now_filter'])
def now_filter_command(message):
    global our_filter
    if our_filter:
        filter_text = ""
        for key, value in our_filter.items():
            filter_text += key + " - " + value[0].upper() + value[1:] + "\n"
        bot.send_message(message.chat.id, 'Текущий фильтр:\n' + filter_text)
    else:
        bot.send_message(message.chat.id, 'Фильтр пуст')


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global last_parsed
    global search_id
    if call.message.message_id == search_id:
        req = call.data.split('_')
        if 'pagination' in req[0]:
            json_string = json.loads(req[0])
            count = json_string['CountPage']
            page = json_string['NumberPage']

            if page == 0:
                page = count
            elif page == count + 1:
                page = 1

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text='<--',
                                                  callback_data="{\"method\":\"pagination\",\"NumberPage\":" +
                                                                str(page - 1) + ",\"CountPage\":" + str(count) + "}"),
                       types.InlineKeyboardButton(text=f'{page}/{count}', callback_data=' '),
                       types.InlineKeyboardButton(text='-->',
                                                  callback_data="{\"method\":\"pagination\",\"NumberPage\":" +
                                                                str(page + 1) + ",\"CountPage\":" + str(count) + "}"))
            cursor.execute(f"SELECT * FROM data_{call.message.chat.id} WHERE id=%s;", (page,))
            res = cursor.fetchone()
            if res:
                if last_parsed == "вакансии":
                    our_id, name, link, salary, company, city, exp = res
                    bot.edit_message_text(f"{name}\n[Ссылка]({link})\n" +
                                          f"Зарплата: {salary}\nОпыт работы: {exp}\nКомпания: {company}\nГород: {city}",
                                          parse_mode="Markdown", reply_markup=markup, chat_id=call.message.chat.id,
                                          message_id=call.message.message_id)
                elif last_parsed == "резюме":
                    our_id, name, link, age, experience, status = res
                    bot.edit_message_text(f"{name}\n[Ссылка]({link})\n" +
                                          f"Возраст: {age}\nСтаж работы: {experience}\n{status}",
                                          parse_mode="Markdown", reply_markup=markup, chat_id=call.message.chat.id,
                                          message_id=call.message.message_id)


@bot.message_handler(content_types=['text'])
def answer(message):
    global site
    global data_type
    global our_filter
    message_text = message.text.lower()
    if message_text in SITES:
        if message_text == "hh.ru":
            site = message_text
            bot.send_message(message.chat.id, 'Сайт выбран')
        else:
            bot.send_message(message.chat.id, 'В данной версии бота сайт не поддерживается')
    elif message_text in DATA_TYPES:
        data_type = message_text
        our_filter = {}
        bot.send_message(message.chat.id, 'Цель парсинга выбрана')
    if data_type:
        if message_text in EXP and len(our_filter.values()) == 0:
            our_filter["Опыт работы"] = message_text
            keyboard = types.ReplyKeyboardMarkup()
            if data_type == "вакансии":
                keyboard.row("Не имеет значения")
                keyboard.row("Не требуется или не указано")
                keyboard.row("Высшее")
                keyboard.row("Среднее профессиональное")
            elif data_type == "резюме":
                keyboard.row("Не имеет значения", "Среднее")
                keyboard.row("Среднее специальное", "Незаконченное высшее")
                keyboard.row("Бакалавр", "Магистр")
                keyboard.row("Высшее", "Кандидат наук")
                keyboard.row("Доктор наук")

            bot.send_message(message.chat.id, 'Выберите уровень образования', reply_markup=keyboard)

        elif (message_text in EDUCATION_V and data_type == "вакансии" or
                message_text in EDUCATION_R and data_type == "резюме") and len(our_filter.values()) == 1:
            our_filter["Образование"] = message_text
            keyboard = types.ReplyKeyboardMarkup()
            keyboard.row("Не имеет значения")
            keyboard.row("Полный день")
            keyboard.row("Сменный график")
            keyboard.row("Вахтовый метод")
            keyboard.row("Удаленная работа")
            keyboard.row("Гибкий график")
            bot.send_message(message.chat.id, 'Выберите тип занятости', reply_markup=keyboard)

        elif message_text in SCHEDULE and len(our_filter.values()) == 2:
            our_filter["График работы"] = message_text
            keyboard = types.ReplyKeyboardMarkup()
            keyboard.row("HH.ru", "Avito", "Habr")
            keyboard.row("Вакансии", "Резюме")
            bot.send_message(message.chat.id, "Фильтры выставлены", reply_markup=keyboard)


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)
