import telebot
from telebot import types
from datetime import datetime
import connector_bitrix as c_bit
from pathlib import Path
import Settings as set

dir_name_logs = str(Path(__file__).parents[1]) + '\logs\logs.txt'

#########

bot = telebot.TeleBot(set.inspection_tokken, parse_mode=None)

users = {}


class User:
    def __init__(self, chat_id, first_name, id_tg_user):
        self.chat_id = chat_id
        self.first_name = first_name
        self.id_tg_user = id_tg_user
        self.id_bitrix_user = None  # [Id, ФИО]
        self.area = None
        self.works_name = None
        self.works_id = None
        self.photo = None
        self.comment = None


def makeList(some_list):  # добавить row_with как аргумент для индивидуального подхода кнопок
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, )  # one_time_keyboard=True
    if some_list:
        bnt_add = []
        for indx, i in enumerate(some_list):
            bnt_add.append(types.KeyboardButton(text=i))
        return markup.add(*bnt_add)
    else:
        return types.ReplyKeyboardRemove()


######################

@bot.message_handler(commands=['start'])
def greetings(message):
    """
    Регистрация / проверка пользователя > начало пути > очистка меню
    """
    users["{0}".format(message.chat.id)] = User(message.chat.id, message.from_user.first_name, message.from_user.id)
    if c_bit.get_user(users["{0}".format(message.chat.id)].id_tg_user):
        users["{0}".format(message.chat.id)].id_bitrix_user = c_bit.get_user(
            users["{0}".format(message.chat.id)].id_tg_user)
        bot.send_message(chat_id=users["{0}".format(message.chat.id)].chat_id,
                         text=f'Привет, {users["{0}".format(message.chat.id)].first_name}\n'
                              f'/start_crawl что бы начать обход',
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, choice_area)
    else:
        bot.send_message(chat_id=users["{0}".format(message.chat.id)].chat_id,
                         text=f'Пользователь, '
                              f'{users["{0}".format(message.chat.id)].first_name} [{users["{0}".format(message.chat.id)].id_tg_user}] '
                              f'не зарегестрирован\n',
                         reply_markup=types.ReplyKeyboardRemove())


def check_stop(message):
    if message.text == '/stop':
        return True
    else:
        return False


def choice_area(message):
    """
    Начало обхода > формируется площадки для пользователя > и выбор площадки > переход на выбор название работ
    """
    if message.text == '/start_crawl':
        if c_bit.get_area_or_work(users["{0}".format(message.chat.id)].id_bitrix_user):
            bot.send_message(chat_id=users["{0}".format(message.chat.id)].chat_id,
                             text=users["{0}".format(message.chat.id)].first_name + ", Выберите площадку",
                             reply_markup=makeList(
                                 c_bit.get_area_or_work(users["{0}".format(message.chat.id)].id_bitrix_user)))
            bot.register_next_step_handler(message, choice_work_type)
        else:
            bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                             "Для вас нет работ.\nДля новой операции напишите\n/start",
                             reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(users["{0}".format(message.chat.id)].chat_id, 'Напиши /start_crawl ')
        bot.register_next_step_handler(message, choice_area)


def choice_work_type(message):  # < Площадка
    """
    :param message: Выбранная площадка из функции choice_area() + записываем площадку в класс
    :return выбираем название работ на основе пользователя и площадки > формируется список работ для выбора
    """
    msg: str = message.text
    if msg in c_bit.get_area_or_work(users["{0}".format(message.chat.id)].id_bitrix_user):
        users["{0}".format(message.chat.id)].area = msg  # записываем площадку
        bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                         f'Выбрана площадка: {str(users["{0}".format(message.chat.id)].area)}\n'
                         f'*Выберите* тип работ:',
                         reply_markup=makeList(
                             c_bit.get_area_or_work(users["{0}".format(message.chat.id)].id_bitrix_user,
                                                    name_area=msg)),
                         parse_mode='Markdown')
        bot.register_next_step_handler(message, choice_comment)
    else:
        if check_stop(message):
            make_choice_end(message)
        else:
            bot.send_message(users["{0}".format(message.chat.id)].chat_id, 'Надо выбрать площадку из списка')
            bot.register_next_step_handler(message, choice_work_type)


def choice_comment(message):
    """
    :param message: Выбранный тип работ из функции choice_work_type() + записываем тип работ в класс
    :return Проверка на выбор тип работ что бы пользователь не ввел что-то свое, а выбирал только из меню
        > записывает в класс пользователя название работ > определяем Id работ
        > проверка есть ли замечания all_comments, от этого зависит наполнение меню выбора
        > выводит количество замечаний > формирует список для выбора "показать все замечания"
        > выводим меню для выбора что делать дальше и как быть с этой работой
    """
    msg: str = message.text
    if msg in c_bit.get_area_or_work(users["{0}".format(message.chat.id)].id_bitrix_user,
                                     name_area=users["{0}".format(message.chat.id)].area):
        users["{0}".format(message.chat.id)].works_name = msg
        # Записываем id работы в класс
        work_id = c_bit.get_id_work(
            users["{0}".format(message.chat.id)].id_bitrix_user,
            users["{0}".format(message.chat.id)].area,
            users["{0}".format(message.chat.id)].works_name)
        users["{0}".format(message.chat.id)].works_id = work_id
        # Проверяем если замечания уже есть то мы не можем ответить "нет замечаний"
        all_comments = c_bit.get_reg_list(work_id)
        choice_list = ['Добавить замечание',
                       'Посмотреть замечания' if all_comments else 'Нет новых замечаний',
                       'Принять работу',
                       'Выбрать другой тип работ',  # ok
                       'Нет новых замечаний']  # ok
        bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                         f'Тип работ: {str(users["{0}".format(message.chat.id)].works_name)}\n'
                         f'{"Количество замечаний: " if all_comments else "Нет активных замечаний, ваши действия?"} '
                         f'{len(all_comments) if all_comments else ""}',
                         reply_markup=makeList(
                             choice_list if all_comments else choice_list[0:-1]))  # types.ReplyKeyboardRemove()
        bot.register_next_step_handler(message, choice_comment_final)
    else:
        if check_stop(message):
            make_choice_end(message)
        else:
            bot.send_message(users["{0}".format(message.chat.id)].chat_id, 'Надо выбрать тип работ из списка')
            bot.register_next_step_handler(message, choice_comment)


def choice_comment_final(message):
    """param message: тот ответ который был в функции choice_comment()"""
    msg: str = message.text.lower() if message.text else message.text
    all_comments = c_bit.get_reg_list(users["{0}".format(message.chat.id)].works_id)
    if msg == 'добавить замечание':
        bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                         text="Напишите замечание (не более 100 символов):",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_comment)
    elif msg == 'нет новых замечаний' or msg == 'нет замечаний':
        message.text = 'Без изменений, отметится'
        get_comment(message)
    elif msg == 'посмотреть замечания':
        for i in all_comments:
            keyboard_full = types.InlineKeyboardMarkup(row_width=2)
            keyboard_only_photo = types.InlineKeyboardMarkup(row_width=2)
            key_yes = types.InlineKeyboardButton(text='Принять',
                                                 callback_data=f'{str(i[0])}|Принять|'
                                                               f'{str(users["{0}".format(message.chat.id)].chat_id)}')
            key_no = types.InlineKeyboardButton(text='Отклонить',
                                                callback_data=f'{str(i[0])}|Отклонить|'
                                                              f'{str(users["{0}".format(message.chat.id)].chat_id)}')
            key_photo = types.InlineKeyboardButton(text='Показать фото (если есть)',
                                                   callback_data=f'{str(i[0])}|Фото|'
                                                                 f'{str(users["{0}".format(message.chat.id)].chat_id)}')
            keyboard_full.add(key_yes, key_no, key_photo)
            keyboard_only_photo.add(key_photo)
            bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                             f'id {str(i[0])}: {str(i[4])[0:100]}'  # id и комментарий замечания
                             f'{"...[ещё " + str(len(str(i[6])) - 99) + " символа]" if len(str(i[6])) > 100 else ""}\n'
                             f'Замечание сделано - {str(i[2])[0:10]}\n'
                             f'Статус - {c_bit.replace_status_name(i[3]) if i[3] is not None else "Нет"}\n'
                             f'Плановая дата - {str(i[6])[0:10] if i[6] is not None else "Нет"}\n',
                             reply_markup=keyboard_full if i[3] == set.ST_SM_INCONFIRM else keyboard_only_photo)
        bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                         "Список сформирован" if all_comments else "Нет замечаний",
                         parse_mode='Markdown')
        bot.register_next_step_handler(message, choice_comment_final)

    elif msg == 'принять работу':  # если не все замечание исправлены и подтверждены, то нельзя принять работу
        if c_bit.get_reg_list(users["{0}".format(message.chat.id)].works_id):
            bot.send_message(users["{0}".format(message.chat.id)].chat_id, "есть не закрытые замечания")
            bot.register_next_step_handler(message, choice_comment_final)
        else:
            # обновление статуса по маршруту
            c_bit.update_status_route(users["{0}".format(message.chat.id)].works_id)
            choice_list = ['Выбрать другую площадку', 'Завершить обход']

            bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                             f'Работа "{users["{0}".format(message.chat.id)].works_name}"\n'
                             f'Закрыт.\n'
                             f'Что делаем дальше?',
                             reply_markup=makeList(choice_list))
            bot.register_next_step_handler(message, make_choice_end)

    elif msg == 'без изменений, отметится':
        users["{0}".format(message.chat.id)].comment = message.text
        get_comment(message)

    elif msg == 'выбрать другой тип работ':
        bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                         "*Выберите* тип работ:\n",
                         reply_markup=makeList(
                             c_bit.get_area_or_work(users["{0}".format(message.chat.id)].id_bitrix_user,
                                                    name_area=users["{0}".format(message.chat.id)].area)),
                         parse_mode='Markdown')
        bot.register_next_step_handler(message, choice_comment)
    else:
        if check_stop(message):
            make_choice_end(message)
        else:
            bot.send_message(users["{0}".format(message.chat.id)].chat_id, text="Сделайте выбор из списка")
            bot.register_next_step_handler(message, choice_comment_final)


# узнаем какую кнопку нажал пользователь
@bot.callback_query_handler(func=lambda call: call.data in
                                              [f'{str(i[0])}|'
                                               f'Принять|'
                                               f'{str(users["{0}".format(call.message.chat.id)].chat_id)}' for i in
                                               c_bit.get_reg_list(
                                                   users["{0}".format(call.message.chat.id)].works_id)]
                                              + [f'{str(i[0])}|'
                                                 f'Отклонить|'
                                                 f'{str(users["{0}".format(call.message.chat.id)].chat_id)}' for i in
                                                 c_bit.get_reg_list(
                                                     users["{0}".format(call.message.chat.id)].works_id)]
                                              + [f'{str(i[0])}|'
                                                 f'Фото|'
                                                 f'{str(users["{0}".format(call.message.chat.id)].chat_id)}' for i in
                                                 c_bit.get_reg_list(
                                                     users["{0}".format(call.message.chat.id)].works_id)]
                                              + [f'|'
                                                 f'{set.IN_LINE_KEY_HIDE}|'
                                                 f'{str(users["{0}".format(call.message.chat.id)].chat_id)}'])
def callback_update(call):
    split_call_data = str(call.data).split('|')
    if call.data == call.data:  # call.data это callback_data
        if split_call_data[1] == "Принять":
            c_bit.confirm_coment(split_call_data[0])
            bot.delete_message(users["{0}".format(call.message.chat.id)].chat_id,
                               message_id=call.message.message_id)
            bot.send_message(users["{0}".format(call.message.chat.id)].chat_id,
                             f'Подтверждено устранение замечания №{split_call_data[0]}')
        elif split_call_data[1] == "Отклонить":
            c_bit.confirm_coment(split_call_data[0], confirm=False)

            bot.delete_message(users["{0}".format(call.message.chat.id)].chat_id,
                               message_id=call.message.message_id)
            bot.send_message(users["{0}".format(call.message.chat.id)].chat_id,
                             f'Вернули в работу замечания №{split_call_data[0]}')
        elif split_call_data[1] == "Фото":
            del_keyboard = types.InlineKeyboardMarkup(row_width=1)  # наша клавиатура
            key_del = types.InlineKeyboardButton(text=set.IN_LINE_KEY_HIDE,
                                                 callback_data=
                                                 f'|'
                                                 f'{set.IN_LINE_KEY_HIDE}|'
                                                 f'{str(users["{0}".format(call.message.chat.id)].chat_id)}')
            del_keyboard.add(key_del)
            img = c_bit.get_comment_photo_url(split_call_data[0])
            if img:
                bot.send_photo(chat_id=users["{0}".format(call.message.chat.id)].chat_id,
                               photo=img,
                               caption=f"фото к замечанию {split_call_data[0]}",
                               reply_markup=del_keyboard,
                               parse_mode="HTML"
                               )
        elif split_call_data[1] == set.IN_LINE_KEY_HIDE:
            bot.delete_message(users["{0}".format(call.message.chat.id)].chat_id,
                               message_id=call.message.message_id)


def get_comment(message):  # Коментарий
    """
    :param message: получение коментария / фото
    :return: обработка соообщения с фото или без и тд.
    """
    msg: str = None
    downloaded_file = None
    if message.content_type == 'photo':
        msg = message.caption if message.caption else 'только фото'
        msg_photo = message.photo[-2].file_id  # [-1] - [-3] Хорошее качество плохое качество
        file_info = bot.get_file(msg_photo)
        downloaded_file = bot.download_file(file_info.file_path)
    else:
        msg = message.text if message.text else 'Нет описания'

    users["{0}".format(message.chat.id)].comment = msg
    users["{0}".format(message.chat.id)].photo = downloaded_file

    question = f'Площадка: {str(users["{0}".format(message.chat.id)].area)}\n' \
               f'Тип работ: {str(users["{0}".format(message.chat.id)].works_name)}\n' \
               f'Коментарий: {str(users["{0}".format(message.chat.id)].comment)[0:100]}' \
               f'{"..." if len(str(users["{0}".format(message.chat.id)].comment)) > 99 else ""}\n' \
               f'Фото: {"есть" if users["{0}".format(message.chat.id)].photo else "без фото"}\n' \
               f'Записать? (да / нет)'
    bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                     text=question,
                     reply_markup=makeList(["Да", 'Нет']))
    bot.register_next_step_handler(message, add_comment)


def add_comment(message):
    """
    :param message: Ответ после обработки сообщения
    :return: Сохраняем в битрикс / создаем смарт процесс замечания
    """
    msg: str = message.text.lower() if message.text else message.text
    # print(users["{0}".format(message.chat.id)].works_id)
    if msg == "да":
        c_bit.save_comment(
            users["{0}".format(message.chat.id)].id_bitrix_user[0],  # инспектор
            users["{0}".format(message.chat.id)].works_id,  # работа
            c_bit.get_field_route_by_id(users["{0}".format(message.chat.id)].works_id, set.FIELD_RESP_WORK),
            # отвественный по маршруту
            users["{0}".format(message.chat.id)].comment  # комментарий
            , users["{0}".format(message.chat.id)].photo)

        bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                         text="Записал" + u"\U0001F91D")
    elif msg == "нет":
        bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                         text="Не записал" + u"\U0000274C")
    else:
        bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                         text="Не записал" + u"\U0000274C")
    choice_list = ['Добавить замечание', 'Выбрать другой тип работ', 'Выбрать другую площадку', 'Завершить обход']
    bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                     "Что делаем дальше?",
                     reply_markup=makeList(choice_list))
    bot.register_next_step_handler(message, make_choice_end)


def make_choice_end(message):
    msg: str = message.text.lower() if message.text else message.text
    if msg == "добавить замечание":
        bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                         f'Добавьте замечание на площадку:\n'
                         f'{users["{0}".format(message.chat.id)].area}\n'
                         f'Тип работ: {users["{0}".format(message.chat.id)].works_name}',
                         reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_comment)

    elif msg == "выбрать другую площадку":
        bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                         "Выберите площадку:\n",
                         reply_markup=makeList(
                             c_bit.get_area_or_work(users["{0}".format(message.chat.id)].id_bitrix_user)
                         )
                         )
        bot.register_next_step_handler(message, choice_work_type)
    elif msg == "выбрать другой тип работ":
        bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                         "Выберите тип работ:\n",
                         reply_markup=makeList(
                             c_bit.get_area_or_work(users["{0}".format(message.chat.id)].id_bitrix_user,
                                                    name_area=users["{0}".format(message.chat.id)].area))
                         )
        bot.register_next_step_handler(message, choice_comment)

    else:
        bot.send_message(users["{0}".format(message.chat.id)].chat_id,
                         "Завершаем обход.\nДля новой операции напишите\n/start",
                         reply_markup=types.ReplyKeyboardRemove())


if __name__ == '__main__':
    while True:
        start_time = datetime.today()
        try:
            @bot.message_handler(content_types=['text'])
            def check_start(message):
                if message.text == '/start':
                    bot.register_next_step_handler(message, greetings)
                else:
                    bot.send_message(chat_id=message.chat.id,
                                     text=f'Произошла ошибка\n'
                                          f'Напишите /start',
                                     reply_markup=types.ReplyKeyboardRemove())
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            end_time = datetime.today()
            tdelta = end_time - start_time
            text_log = f'Бот по инспекция |Время ошибки {str(end_time).split(".")[0]} |' \
                       f'Время работы {str(tdelta).split(".")[0]} |' \
                       f'Ошибка {e}'
            print(text_log)
            with open(dir_name_logs, 'a') as f:
                f.write(f'{text_log}\n')
