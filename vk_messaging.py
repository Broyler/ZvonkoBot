from const import settings, color_values
from utils import file_system, tools

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

    def clear_keyboard(self, user_id, message):
        self.vk_api.messages.send(
            peer_id=user_id,
            message=message,
            keyboard=VkKeyboard.get_empty_keyboard(),
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

            if weekday <= 4:
                today_table = file_system.read('table')[str(user['class'])][user['letter']][weekday]

                message = ''
                
                for lesson_index, lesson in enumerate(today_table):
                    temp_message = lesson if type(lesson) == str else lesson[0] + ', ' + lesson[1]
                    times = [
                        str(file_system.read('calls')[str(user['class'])]['to_lesson'][lesson_index]),
                        str(file_system.read('calls')[str(user['class'])]['from_lesson'][lesson_index]),
                        str(str(datetime.datetime.now().hour) + ':' + str(datetime.datetime.now().minute))
                    ]

                    for i in range(len(times)):
                        times[i] = tools.time(times[i])

                    if times[2] < file_system.read('calls')[str(user['class'])]['from_lesson'][-1] and \
                            tools.time(str(file_system.read('calls')[str(user['class'])]['from_lesson']
                                           [lesson_index-1])) <= \
                            times[2] \
                            <= times[0] \
                            or (lesson_index == 0 and times[2] < tools.time(str(file_system.read('calls')
                                                                                [str(user['class'])]['to_lesson'][0]))):
                        temp_emoji = file_system.read('messages')['EMOJI']['LESSON_WAIT']

                    elif times[2] >= times[1]:
                        temp_emoji = file_system.read('messages')['EMOJI']['LESSON_COMPLETE']

                    elif times[0] <= times[2] < times[1]:
                        temp_emoji = file_system.read('messages')['EMOJI']['LESSON_NOW']

                    else:
                        temp_emoji = file_system.read('messages')['EMOJI']['LESSON_INCOMING']

                    temp_message = str(lesson_index + 1) + ') ' + temp_emoji + ' ' + temp_message + '\n'

                    message += temp_message

            else:
                message = 'Сегодня нет уроков!'

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

    @staticmethod
    def get_lesson_next(user_id):
        user = file_system.read('vk_users').get(str(user_id))

        if user['table']:
            weekday = datetime.datetime.now().weekday()

            if weekday > 4:
                message = file_system.read('messages')['WEEKEND']

            else:

                message = ''
                time_now = tools.time(str(str(datetime.datetime.now().hour) + ':' + str(datetime.datetime.now().minute)))
                lesson_count = len(file_system.read('table')[str(user['class'])][user['letter']][weekday]) - 1
                lesson_end = tools.time(file_system.read('calls')[str(user['class'])]['to_lesson'][lesson_count])

                if time_now >= lesson_end:
                    message = file_system.read('messages')['LESSON_NEXT_FINISHED']

                else:
                    for call_index, call in enumerate(file_system.read('calls')[str(user['class'])]['to_lesson']):
                        call = tools.time(call)
                        if time_now < call:
                            temp_smile = file_system.read('messages')['DAYS'][call_index] + '  '

                            temp_lesson = file_system.read('table')[str(user['class'])][user['letter']][weekday][call_index]

                            if type(temp_lesson) == list:
                                temp_cab = temp_lesson[1]
                                temp_lesson = temp_lesson[0]

                            else:
                                temp_cab = file_system.read('classrooms')[str(user['class'])][user['letter']]

                            temp_now = [int(time_now.split(':')[0]), int(time_now.split(':')[1])]
                            temp_call = [int(call.split(':')[0]), int(call.split(':')[1])]

                            if temp_now[0] < temp_call[0] or temp_now[1] < temp_call[1]:
                                temp_now, temp_call = temp_call, temp_now

                            if temp_now[0] != temp_call[0]:
                                if temp_now[1] < temp_call[1]:
                                    temp_now[0] -= 1
                                    temp_now[1] += 60

                            temp_hour = temp_now[0] - temp_call[0]
                            temp_min = temp_now[1] - temp_call[1]

                            message = temp_smile + 'Урок ' + str(temp_lesson) + ', ' + str(temp_cab) + ' начнётся через '

                            if temp_hour > 0:
                                message += str(temp_hour) + 'ч. '

                            message += str(temp_min) + 'мин.'

                            break

        else:
            message = file_system.read('messages')['NOT_AVAILABLE']

        return message

    def send_lesson_next(self, user_id):
        message = self.get_lesson_next(user_id)

        return self.send(user_id, message)

    def delete_junk(self):
        try:
            self.vk_api.messages.delete(message_ids=list(file_system.read('junk')), delete_for_all=1)

        except:
            pass

        file_system.write('junk', [])

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
            message += str(lesson_index) + ' урок ' + tools.time(calls['to_lesson'][lesson_index - 1]) + \
                       '-' + tools.time(calls['from_lesson'][lesson_index - 1]) + '\n'

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
        user = file_system.read('vk_users')[str(user_id)]
        keyboard = dict(file_system.read('keyboards')['SETTINGS_MENU'])
        push = user['push']

        if user['table']:
            keyboard['buttons'][1][0][1] = "GREEN" if push[0] == 1 else "WHITE"
            keyboard['buttons'][1][1][1] = "GREEN" if push[1] == 1 else "WHITE"
            keyboard['buttons'][2][0][1] = "GREEN" if push[2] == 1 else "WHITE"
            keyboard['buttons'][2][1][1] = "GREEN" if push[3] == 1 else "WHITE"

        else:
            keyboard['buttons'][1][0][1] = "GREEN" if push[0] == 1 else "WHITE"
            keyboard['buttons'][1][1][1] = "GREEN" if push[1] == 1 else "WHITE"
            keyboard['buttons'][2][0][1] = "GREEN" if push[2] == 1 else "WHITE"
            temp_a = [keyboard['buttons'][2][0], keyboard['buttons'][3][0]]
            keyboard['buttons'][2] = temp_a
            temp_b = [keyboard['buttons'][3][1]]
            keyboard['buttons'][3] = temp_b

        self.send_keyboard(user_id, keyboard, message, True)

    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                data = event.object.get('message')

                if data['text'] == 'admin:stop_bot' and data['from_id'] in file_system.read('admins'):
                    file_system.log('log', '[admin] Администратор ' + str(data['from_id']) + ' остановил бота.')
                    exit(0)

                elif data['text'] == 'admin:statistics' and data['from_id'] in file_system.read('admins'):
                    msg = 'Подписчиков группы: ' + str(self.vk_api.groups.getMembers(
                        group_id=settings.vk_group_id
                    )['count']) + '\nПользователей: ' + str(len(file_system.read('vk_users')))
                    self.send(data['from_id'], msg)

                elif data['text'] == 'admin:reset_users' and data['from_id'] in file_system.read('admins'):
                    file_system.log('log', '[admin] Администратор ' + str(data['from_id']) + ' сбросил пользователей.')
                    file_system.write('vk_users', {})
                    continue
                    
                elif data['text'] == 'admin:delete_junk' and data['from_id'] in file_system.read('admins'):
                    file_system.log('log', '[admin] Администратор ' + str(data['from_id']) + ' deleted junk')
                    self.delete_junk()
                    self.send(data['from_id'], 'Junk has been deleted')
                    continue
                    
                elif data['text'] == 'admin:measure_temp' and data['from_id'] in file_system.read('admins'):
                    self.send(data['from_id'], 'Temp: ' + str(tools.temp()) + '°C')
                    continue

                elif data['text'].split()[0] == 'admin:send_all':
                    for user_id in file_system.read('vk_users'):
                        try:
                            self.send(user_id, str(' '.join(data['text'].split()[1::])))

                        except vk_api.exceptions.ApiError:
                            file_system.log('log', '[warning] Не удалось отправить рассылку для ID: ' + str(user_id))

                    continue

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
                            file_system.update_user(str(data['from_id']), 'push', [0, 0, 0, 0, 2])

                        else:
                            self.send(data['from_id'], file_system.read('messages')['REGISTER_WRONG_PUSH'])

                        if push_set:
                            if not user['table']:
                                new_push = file_system.read('vk_users')[str(data['from_id'])]['push']
                                new_push[3] = 0
                                file_system.update_user(str(data['from_id']), 'push', new_push)

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
                        ] if user['table'] else [
                            file_system.read('keyboards')['SETTINGS_MENU']['buttons'][1][0][0],
                            file_system.read('keyboards')['SETTINGS_MENU']['buttons'][1][1][0],
                            file_system.read('keyboards')['SETTINGS_MENU']['buttons'][2][0][0]]

                        if data['text'] == file_system.read('keyboards')['SETTINGS_MENU']['buttons'][3][1][0]:
                            file_system.update_user(str(data['from_id']), 'state', file_system.read('states')['IDLE'])
                            self.send_keyboard(data['from_id'], 'MENU', 'Вы вернулись в меню')

                        elif data['text'] == file_system.read('keyboards')['SETTINGS_MENU']['buttons'][0][0][0]:
                            file_system.update_user(str(data['from_id']), 'state',
                                                    file_system.read('states')['IDLE_SETTINGS_MINUTES'])
                            self.send_keyboard_minutes(str(data['from_id']), 'Чтобы вернуться назад нажмите кнопку '
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
