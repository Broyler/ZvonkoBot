from const import settings, color_values
from utils import file_system

from random import randint
from sys import exit
import datetime

import vk_api.vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import os
import dialogflow
from google.api_core.exceptions import InvalidArgument

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'cloud-key.json'

DIALOGFLOW_PROJECT_ID = 'zvonkobot'
DIALOGFLOW_LANGUAGE_CODE = 'ru'
SESSION_ID = 'random'

session_client = dialogflow.SessionsClient()
session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)


# Todo: +другие корпуса

# Todo: --> мульти-выбор минут


class Server:
    def __init__(self):
        self.vk = vk_api.VkApi(token=settings.vk_api_token)
        self.long_poll = VkBotLongPoll(self.vk, settings.vk_group_id)
        self.vk_api = self.vk.get_api()

    def send(self, user_id, message):
        return self.vk_api.messages.send(
            peer_id=user_id,
            message=message,
            random_id=randint(-100000, 100000)
        )

    def send_keyboard(self, user_id, keyboard_id, message, raw=False):
        data = file_system.read('keyboards').get(keyboard_id) if not raw else keyboard_id
        keyboard = VkKeyboard(one_time=data['one_time'])

        for button_row in data['buttons']:
            for button in button_row:
                keyboard.add_button(label=button[0], color=color_values.colors.get(button[1]))

            if data['buttons'][-1] != button_row:
                keyboard.add_line()

        self.vk_api.messages.send(
            peer_id=user_id,
            message=message,
            keyboard=keyboard.get_keyboard(),
            random_id=randint(-100000, 100000)
        )

    def send_letter_keyboard(self, user_id, message, cancel_btn):
        try:
            class_id = file_system.read('vk_users')[user_id]['class']

        except IndexError:
            print('[error] Invalid element index')
            return None

        keyboard = VkKeyboard()
        buttons = file_system.read('commands')['letter_select'][class_id]

        for button in buttons:
            if (buttons.index(button) + 2) % 4 == 0:
                keyboard.add_line()

            keyboard.add_button(label=button, color=VkKeyboardColor.PRIMARY)

        if cancel_btn:
            keyboard.add_line()
            keyboard.add_button(label='Назад', color=VkKeyboardColor.NEGATIVE)

        self.vk_api.messages.send(
            peer_id=user_id,
            message=message,
            keyboard=keyboard.get_keyboard(),
            random_id=randint(-100000, 100000)
        )

    def send_subscribe(self, user_id):
        if self.vk_api.groups.isMember(group_id=settings.vk_group_id, user_id=user_id) == 0:
            msg = file_system.read('messages')['SUBSCRIBE_TEMPLATE'] + \
                  str(self.vk_api.groups.getMembers(group_id=settings.vk_group_id)['count']) + \
                  " человек, а ботом пользуются " + str(len(file_system.read('vk_users'))) + \
                  ".\n-Разработчики"
            self.send(user_id, msg)

        else:
            return 0

    def send_table_today(self, user_id):
        user = file_system.read('vk_users').get(str(user_id))

        if user['table']:
            weekday = datetime.datetime.now().weekday()
            today_table = file_system.read('table')[str(user['class'])][user['letter']][weekday]

            message = ''

            for lesson_index, lesson in enumerate(today_table):
                temp_message = lesson if type(lesson) == str else lesson[0] + ', ' + lesson[1]
                times = [
                    str(file_system.read('calls')[str(user['class'])]['to_lesson'][lesson_index]),
                    str(file_system.read('calls')[str(user['class'])]['from_lesson'][lesson_index]),
                    str(str(datetime.datetime.now().hour) + ':' + str(datetime.datetime.now().minute))
                ]

                temp_emoji = ''

                for time_index, element in enumerate(times):
                    if element[-2] == ':':
                        times[time_index] = element[0:-2] + ':0' + element[-1]

                    if element[1] == ':':
                        times[time_index] = '0' + times[time_index]

                    if times[2] < file_system.read('calls')[str(user['class'])]['from_lesson'][-1] and times[1] <= \
                            times[2] \
                            <= str(file_system.read('calls')[str(user['class'])]['to_lesson'][lesson_index + 1]):
                        temp_emoji = file_system.read('messages')['EMOJI']['LESSON_WAIT']

                    elif times[2] > times[1]:
                        temp_emoji = file_system.read('messages')['EMOJI']['LESSON_COMPLETE']

                    elif times[0] <= times[2] <= times[1]:
                        temp_emoji = file_system.read('messages')['EMOJI']['LESSON_NOW']

                    else:
                        temp_emoji = file_system.read('messages')['EMOJI']['LESSON_INCOMING']

                temp_message = str(lesson_index + 1) + ') ' + temp_emoji + ' ' + temp_message + '\n'

                message += temp_message

            self.send(user_id, message)

        else:
            self.send(user_id, file_system.read('messages')['NOT_AVAILABLE'])

    def send_table_week(self, user_id):
        user = file_system.read('vk_users').get(str(user_id))

        if user['table']:
            table = file_system.read('table')[str(user['class'])][user['letter']]
            message = ''

            for day in table:
                message += file_system.read('messages')['WEEKDAYS'][table.index(day)] + '\n'

                for lesson in day:
                    temp_message = lesson if type(lesson) == str else lesson[0] + ', ' + lesson[1]
                    message += temp_message + '\n'

                message += '\n'

            self.send(user_id, message)

        else:
            self.send(user_id, file_system.read('messages')['NOT_AVAILABLE'])

    def send_lesson_next(self, user_id):
        user = file_system.read('vk_users').get(str(user_id))

        if user['table']:
            weekday = datetime.datetime.now().weekday()
            today_table = file_system.read('table')[str(user['class'])][user['letter']][weekday]
            message = ''

            for lesson_index, lesson in enumerate(today_table):
                times = [
                    str(file_system.read('calls')[str(user['class'])]['to_lesson'][lesson_index]),
                    str(str(datetime.datetime.now().hour) + ':' + str(datetime.datetime.now().minute))
                ]

                for time_index, element in enumerate(times):
                    if element[-2] == ':':
                        times[time_index] = element[0:-2] + ':0' + element[-1]

                    if element[1] == ':':
                        times[time_index] = '0' + times[time_index]

                hour_dist = int(times[0].split(':')[0]) - int(times[1].split(':')[0])
                minute_dist = int(times[0].split(':')[1]) - int(times[1].split(':')[1])

                if hour_dist <= 0 and minute_dist >= 0:
                    time_msg = str(minute_dist) + ' мин.'

                else:
                    time_msg = str(hour_dist) + ' ч. ' + str(minute_dist) + ' мин.'

                if hour_dist >= 0 and minute_dist >= 0:
                    if type(lesson) == list:
                        message = 'Урок ' + lesson[0] + ', ' + lesson[1] + ' начнется через ' + time_msg

                    else:
                        message = 'Урок ' + lesson + ', ' + \
                                  str(file_system.read('classrooms')[str(user['class'])][user['letter']]) + \
                                  ' начнется через ' + time_msg

                    break

                else:
                    message = file_system.read('messages')['LESSON_NEXT_FINISHED']

            return self.send(user_id, message)

        else:
            return self.send(user_id, file_system.read('messages')['NOT_AVAILABLE'])

    def delete_junk(self):
        self.vk_api.messages.delete(message_ids=file_system.read('junk'), delete_for_all=1)

    def send_table_tomorrow(self, user_id):
        user = file_system.read('vk_users').get(str(user_id))

        if user['table']:
            weekday = datetime.datetime.now().weekday()

            if weekday >= 4:
                prefix = 'Завтра нет уроков, вот расписание на понедельник\n\n'
                weekday = 0

            else:
                weekday += 1
                prefix = file_system.read('messages')['WEEKDAYS'][weekday] + '\n\n'

            table = file_system.read('table')[str(user['class'])][user['letter']][weekday]
            message = prefix

            for lesson in table:
                temp_message = lesson if type(lesson) == str else lesson[0] + ', ' + lesson[1]
                message += str(table.index(lesson) + 1) + ') ' + temp_message + '\n'

            self.send(user_id, message)

        else:
            self.send(user_id, file_system.read('messages')['NOT_AVAILABLE'])

    def send_calls(self, user_id):
        user = file_system.read('vk_users')[str(user_id)]
        calls = file_system.read('calls')[str(user['class'])]
        message = ''

        for lesson_index in range(1, len(calls['to_lesson']) + 1):
            message += str(lesson_index) + ' урок ' + calls['to_lesson'][lesson_index - 1] + \
                       '-' + calls['from_lesson'][lesson_index - 1] + '\n'

        self.send(user_id, message)

    def send_keyboard_minutes(self, user_id, message):
        keyboard = file_system.read('keyboards')['MINUTES_MENU']
        push = file_system.read('vk_users')[user_id]['push'][4]

        if push == 1:
            keyboard['buttons'][0][0][1] = "GREEN"

        elif push == 2:
            keyboard['buttons'][0][1][1] = "GREEN"

        elif push == 3:
            keyboard['buttons'][0][2][1] = "GREEN"

        elif push == 4:
            keyboard['buttons'][1][0][1] = "GREEN"

        else:
            keyboard['buttons'][1][1][1] = "GREEN"

        self.send_keyboard(user_id, keyboard, message, True)

    def send_keyboard_settings(self, user_id, message):
        keyboard = file_system.read('keyboards')['SETTINGS_MENU']
        push = file_system.read('vk_users')[str(user_id)]['push']

        keyboard['buttons'][1][0][1] = "GREEN" if push[0] == 1 else "WHITE"
        keyboard['buttons'][1][1][1] = "GREEN" if push[1] == 1 else "WHITE"
        keyboard['buttons'][2][0][1] = "GREEN" if push[2] == 1 else "WHITE"
        keyboard['buttons'][2][1][1] = "GREEN" if push[3] == 1 else "WHITE"

        self.send_keyboard(user_id, keyboard, message, True)

    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                data = event.object.get('message')

                if data['text'] == 'admin:stop_bot' and data['from_id'] in file_system.read('admins'):
                    file_system.log('log', '[admin] Администратор ' + str(data['from_id']) + ' остановил бота.')
                    exit(0)

                elif data['text'] == 'admin:reset_users' and data['from_id'] in file_system.read('admins'):
                    file_system.log('log', '[admin] Администратор ' + str(data['from_id']) + ' сбросил пользователей.')
                    file_system.write('vk_users', {})

                elif data['text'].split()[0] == 'admin:send_all':
                    for user_id in file_system.read('vk_users'):
                        self.send(user_id, str(' '.join(data['text'].split()[1::])))

                if str(data['from_id']) in file_system.read('vk_users'):
                    user = file_system.read('vk_users').get(str(data['from_id']))

                    if int(user['state']) == file_system.read('states')['REGISTER_CLASS']:
                        if user['table']:
                            if data['text'] in file_system.read('commands')['letter_select']:
                                file_system.update_user(str(data['from_id']), 'class', data['text'])
                                file_system.update_user(str(data['from_id']), 'state',
                                                        file_system.read('states')['REGISTER_LETTER'])
                                self.send_letter_keyboard(str(data['from_id']),
                                                          file_system.read('messages')['REGISTER_LETTER'], False)

                            else:
                                self.send(data['from_id'], file_system.read('messages')['REGISTER_WRONG_CLASS'])

                        else:
                            if data['text'] in file_system.read('commands')['letter_select_others']:
                                file_system.update_user(str(data['from_id']), 'class', data['text'])
                                file_system.update_user(str(data['from_id']), 'state',
                                                        file_system.read('states')['REGISTER_PUSH'])
                                self.send_keyboard(str(data['from_id']), 'REGISTER_PUSH',
                                                   file_system.read('messages')['REGISTER_PUSH'])

                            else:
                                self.send(data['from_id'], file_system.read('messages')['REGISTER_WRONG_CLASS'])

                    elif int(user['state'] == file_system.read('states')['REGISTER_LETTER']):
                        if data['text'] in file_system.read('commands')['letter_select'][user['class']]:
                            file_system.update_user(str(data['from_id']), 'letter', data['text'])
                            file_system.update_user(str(data['from_id']), 'state',
                                                    file_system.read('states')['REGISTER_PUSH'])
                            self.send_keyboard(data['from_id'], "REGISTER_PUSH",
                                               file_system.read('messages')['REGISTER_PUSH'])

                        else:
                            self.send(data['from_id'], file_system.read('messages')['REGISTER_WRONG_LETTER'])

                    elif int(user['state']) == file_system.read('states')['IDLE_SETTINGS_CLASS']:
                        if data['text'] in file_system.read('commands')['letter_select']:
                            file_system.update_user(str(data['from_id']), 'class', data['text'])
                            file_system.update_user(str(data['from_id']), 'state',
                                                    file_system.read('states')['IDLE_SETTINGS_LETTER'])
                            self.send_letter_keyboard(str(data['from_id']),
                                                      file_system.read('messages')['REGISTER_LETTER'], False)

                        else:
                            self.send(data['from_id'], file_system.read('messages')['REGISTER_WRONG_CLASS'])

                    elif int(user['state'] == file_system.read('states')['IDLE_SETTINGS_LETTER']):
                        if data['text'] in file_system.read('commands')['letter_select'][user['class']]:
                            file_system.update_user(str(data['from_id']), 'letter', data['text'])
                            file_system.update_user(str(data['from_id']), 'state',
                                                    file_system.read('states')['IDLE_SETTINGS'])
                            self.send_keyboard_settings(data['from_id'], 'Вы успешно изменили свой класс')

                        else:
                            self.send(data['from_id'], file_system.read('messages')['REGISTER_WRONG_LETTER'])

                    elif int(user['state']) == file_system.read('states')['REGISTER_PUSH']:
                        push_set = False

                        if data['text'] == file_system.read('keyboards')['REGISTER_PUSH']['buttons'][0][0][0]:
                            push_set = True
                            file_system.update_user(str(data['from_id']), 'push',
                                                    file_system.read('states')['PUSH_STANDARD'])

                        elif data['text'] == file_system.read('keyboards')['REGISTER_PUSH']['buttons'][0][1][0]:
                            push_set = True

                        else:
                            self.send(data['from_id'], file_system.read('messages')['REGISTER_WRONG_PUSH'])

                        if push_set:
                            file_system.update_user(str(data['from_id']), 'state', file_system.read('states')['IDLE'])
                            self.send_keyboard(data['from_id'], 'MENU',
                                               file_system.read('messages')['REGISTER_COMPLETE'])
                            self.send_subscribe(data['from_id'])

                    elif int(user['state']) == file_system.read('states')['IDLE']:
                        if data['text'] == file_system.read('keyboards')['MENU']['buttons'][0][0][0]:
                            self.send_table_today(str(data['from_id']))

                        elif data['text'] == file_system.read('keyboards')['MENU']['buttons'][0][1][0]:
                            self.send_lesson_next(str(data['from_id']))

                        elif data['text'] == file_system.read('keyboards')['MENU']['buttons'][1][0][0]:
                            file_system.update_user(str(data['from_id']), 'state',
                                                    file_system.read('states')['IDLE_TABLE'])
                            self.send_keyboard(data['from_id'], 'TABLE_MENU', 'Чтобы вернуться обратно, нажмите '
                                                                              'кнопку \"Назад\"')

                        elif data['text'] == file_system.read('keyboards')['MENU']['buttons'][2][0][0]:
                            file_system.update_user(str(data['from_id']), 'state',
                                                    file_system.read('states')['IDLE_SETTINGS'])
                            self.send_keyboard_settings(str(data['from_id']), 'Чтобы вернуться обратно нажмите '
                                                                              'кнопку \"Назад\"')

                        else:
                            # noinspection PyUnresolvedReferences
                            text_input = dialogflow.types.TextInput(text=data['text'],
                                                                    language_code=DIALOGFLOW_LANGUAGE_CODE)
                            # noinspection PyUnresolvedReferences
                            query_input = dialogflow.types.QueryInput(text=text_input)

                            try:
                                response = session_client.detect_intent(session=session, query_input=query_input)
                                self.send(data['from_id'], response.query_result.fulfillment_text)

                            except InvalidArgument:
                                pass

                        """
                        elif data['text'] == file_system.read('keyboards')['MENU']['buttons'][1][1][0]:
                            file_system.update_user(str(data['from_id']), 'state', file_system.read('states')['GAME'])
                            self.send_keyboard(data['from_id'], 'GAME', 'Я загадаю случайное число от 1 до 5, и если '
                                                                        'ты его угадаешь, то получишь 4 монеты, '
                                                                        'а если не угадаешь, то проиграешь 1 монету')"""

                    elif int(user['state']) == file_system.read('states')['IDLE_TABLE']:
                        if data['text'] == file_system.read('keyboards')['TABLE_MENU']['buttons'][2][0][0]:
                            file_system.update_user(str(data['from_id']), 'state', file_system.read('states')['IDLE'])
                            self.send_keyboard(data['from_id'], 'MENU', 'Вы успешно вернулись в меню')

                        elif data['text'] == file_system.read('keyboards')['TABLE_MENU']['buttons'][1][0][0]:
                            self.send_table_week(str(data['from_id']))

                        elif data['text'] == file_system.read('keyboards')['TABLE_MENU']['buttons'][0][0][0]:
                            self.send_table_tomorrow(str(data['from_id']))

                        elif data['text'] == file_system.read('keyboards')['TABLE_MENU']['buttons'][0][1][0]:
                            self.send_calls(str(data['from_id']))

                        else:
                            self.send(data['from_id'], file_system.read('messages')['IDLE_TABLE_WRONG'])

                    elif int(user['state']) == file_system.read('states')['IDLE_SETTINGS']:
                        settings_buttons = [
                            file_system.read('keyboards')['SETTINGS_MENU']['buttons'][1][0][0],
                            file_system.read('keyboards')['SETTINGS_MENU']['buttons'][1][1][0],
                            file_system.read('keyboards')['SETTINGS_MENU']['buttons'][2][0][0],
                            file_system.read('keyboards')['SETTINGS_MENU']['buttons'][2][1][0]
                        ]

                        if data['text'] == file_system.read('keyboards')['SETTINGS_MENU']['buttons'][3][1][0]:
                            file_system.update_user(str(data['from_id']), 'state', file_system.read('states')['IDLE'])
                            self.send_keyboard(data['from_id'], 'MENU', 'Вы вернулись в меню')

                        elif data['text'] == file_system.read('keyboards')['SETTINGS_MENU']['buttons'][0][0][0]:
                            file_system.update_user(str(data['from_id']), 'state',
                                                    file_system.read('states')['IDLE_SETTINGS_MINUTES'])
                            self.send_keyboard_minutes(str(data['from_id']), 'Чтобы вернуться назад нажмит кнопку '
                                                                             '\"Назад\"')

                        elif data['text'] == file_system.read('keyboards')['SETTINGS_MENU']['buttons'][3][0][0]:
                            file_system.update_user(str(data['from_id']), 'state',
                                                    file_system.read('states')['REGISTER_BUILDING'])
                            self.send_keyboard(str(data['from_id']), 'BUILDING_1519',
                                               file_system.read('messages')['REGISTER_WRONG_BUILDING'])

                        elif data['text'] in settings_buttons:
                            push = file_system.read('vk_users')[str(data['from_id'])]['push']
                            push_index = settings_buttons.index(data['text'])
                            push[push_index] = 1 if push[push_index] == 0 else 0

                            file_system.update_user(str(data['from_id']), 'push', push)
                            self.send_keyboard_settings(str(data['from_id']), 'Вы успешно изменили настройки')

                    elif int(user['state']) == file_system.read('states')['IDLE_SETTINGS_MINUTES']:
                        if data['text'] == file_system.read('keyboards')['MINUTES_MENU']['buttons'][2][0][0]:
                            file_system.update_user(str(data['from_id']), 'state',
                                                    file_system.read('states')['IDLE_SETTINGS'])
                            self.send_keyboard_settings(str(data['from_id']), 'Вы успешно вернулись в настройки')

                        elif data['text'] in file_system.read('commands')['minute_select']:
                            user_push = file_system.read('vk_users')[str(data['from_id'])]['push']
                            user_push[4] = file_system.read('commands')['minute_select'][data['text']]
                            file_system.update_user(str(data['from_id']), 'push', user_push)
                            self.send_keyboard_minutes(str(data['from_id']), 'Вы успешно изменили время отправки '
                                                                             'сообщения')

                    elif int(user['state']) == file_system.read('states')['REGISTER_BUILDING']:
                        if data['text'] == file_system.read('keyboards')['BUILDING_1519']['buttons'][0][0][0]:
                            file_system.update_user(str(data['from_id']), 'table', True)
                            file_system.update_user(str(data['from_id']), 'state',
                                                    file_system.read('states')['REGISTER_CLASS'])
                            self.send_keyboard(data['from_id'], 'REGISTER_CLASS',
                                               file_system.read('messages')['REGISTER_WRONG_CLASS'])

                        elif data['text'] == file_system.read('keyboards')['BUILDING_1519']['buttons'][0][1][0]:
                            file_system.update_user(str(data['from_id']), 'table', False)
                            user = file_system.read('vk_users')[str(data['from_id'])]
                            temp_class = 'REGISTER_CLASS' if user['table'] else 'REGISTER_CLASS_FULL'

                            file_system.update_user(str(data['from_id']), 'state',
                                                    file_system.read('states')['REGISTER_CLASS'])
                            self.send_keyboard(data['from_id'], temp_class,
                                               file_system.read('messages')['REGISTER_WRONG_CLASS'])

                        else:
                            self.send(data['from_id'], file_system.read('messages')['REGISTER_WRONG_BUILDING'])

                    elif int(user['state']) == file_system.read('states')['GAME']:
                        if data['text'] in '12345':
                            if file_system.read('vk_users')[str(data['from_id'])]['coins'] > 0:
                                num = randint(1, 5)

                                if data['text'] == str(num):
                                    msg = 'Вы выиграли! Число: ' + str(num) + '\nБаланс: ' + \
                                          str(file_system.read('vk_users')[str(data['from_id'])]['coins'] + 4) + ' (+4)'
                                    file_system.update_user(str(data['from_id']), 'coins',
                                                            file_system.read('vk_users')[str(data['from_id'])][
                                                                'coins'] + 4)
                                    self.send(data['from_id'], msg)

                                else:
                                    msg = 'Вы проиграли! Число: ' + str(num) + '\nБаланс: ' + \
                                          str(file_system.read('vk_users')[str(data['from_id'])]['coins'] - 1) + ' (-1)'
                                    file_system.update_user(str(data['from_id']), 'coins',
                                                            file_system.read('vk_users')[str(data['from_id'])][
                                                                'coins'] - 1)

                                    self.send(data['from_id'], msg)

                            else:
                                self.send(data['from_id'], 'Увы, у Вас недостаточно монет для игры')

                        elif data['text'] == file_system.read('keyboards')['GAME']['buttons'][1][1][0]:
                            file_system.update_user(str(data['from_id']), 'state', file_system.read('states')['IDLE'])
                            self.send_keyboard(str(data['from_id']), 'MENU', 'Вы успешно вернулись в меню')

                        elif data['text'] == file_system.read('keyboards')['GAME']['buttons'][1][0][0]:
                            msg = 'Таблица лидеров (монетки):\n'
                            scores = []

                            for user_id in file_system.read('vk_users'):
                                user = file_system.read('vk_users')[str(user_id)]
                                scores.append([int(user['coins']), str(user_id)])

                            scores.sort(reverse=True)
                            scores = scores[0:5]

                            for score in scores:
                                user_data = self.vk_api.users.get(user_ids=score[1])[0]
                                msg += str(scores.index(score) + 1) + ' место - @id' + str(score[1]) + ' (' + \
                                       user_data['first_name'] + ' ' + user_data['last_name'] + ') : ' + str(score[0]) \
                                       + ' монет\n'

                            self.send(data['from_id'], msg)

                else:
                    file_system.log('users', 'Зарегистрирован ID ' + str(data['from_id']))
                    self.send(data['from_id'], file_system.read('messages')['REGISTER_GREETING'])
                    file_system.new_user(str(data['from_id']))
                    self.send_keyboard(
                        data['from_id'],
                        "BUILDING_1519",
                        file_system.read('messages').get('REGISTER_WRONG_BUILDING')
                    )
