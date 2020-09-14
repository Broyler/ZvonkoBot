from const import settings, color_values
from utils import file_system

from random import randint
from sys import exit
import datetime

import vk_api.vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


class Server:
    def __init__(self):
        self.vk = vk_api.VkApi(token=settings.vk_api_token)
        self.long_poll = VkBotLongPoll(self.vk, settings.vk_group_id)
        self.vk_api = self.vk.get_api()

    def send(self, user_id, message):
        self.vk_api.messages.send(
            peer_id=user_id,
            message=message,
            random_id=randint(-1000, 1000)
        )

    def send_keyboard(self, user_id, keyboard_id, message):
        data = file_system.read('keyboards').get(keyboard_id)
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
            random_id=randint(-1000, 1000)
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
            keyboard.add_button(label='Отмена', color=VkKeyboardColor.NEGATIVE)

        self.vk_api.messages.send(
            peer_id=user_id,
            message=message,
            keyboard=keyboard.get_keyboard(),
            random_id=randint(-1000, 1000)
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

            for time_index, element in enumerate(times):
                if element[-2] == ':':
                    times[time_index] = element[0:-2] + ':0' + element[-1]

                if element[1] == ':':
                    times[time_index] = '0' + times[time_index]

            temp_message = times[0] + ' - ' + temp_message + '\n'

            if times[2] >= times[1]:
                for char in temp_message:
                    message += '&#0822;' + char

            else:
                message += temp_message

        self.send(user_id, message)

    def send_table_week(self, user_id):
        user = file_system.read('vk_users').get(str(user_id))
        table = file_system.read('table')[str(user['class'])][user['letter']]
        message = ''

        for day in table:
            message += file_system.read('messages')['WEEKDAYS'][datetime.datetime.now().weekday()] + '\n'

            for lesson in day:
                temp_message = lesson if type(lesson) == str else lesson[0] + ', ' + lesson[1]
                message += temp_message + '\n'

            message += '\n'

        self.send(user_id, message)

    def send_lesson_next(self, user_id):
        user = file_system.read('vk_users').get(str(user_id))
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

        self.send(user_id, message)

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

                if str(data['from_id']) in file_system.read('vk_users'):
                    user = file_system.read('vk_users').get(str(data['from_id']))

                    if int(user['state']) == file_system.read('states')['REGISTER_CLASS']:
                        if data['text'] in file_system.read('commands')['letter_select']:
                            file_system.update_user(str(data['from_id']), 'class', data['text'])
                            file_system.update_user(str(data['from_id']), 'state',
                                                    file_system.read('states')['REGISTER_LETTER'])
                            self.send_letter_keyboard(str(data['from_id']),
                                                      file_system.read('messages')['REGISTER_LETTER'], False)

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

                    elif int(user['state']) == file_system.read('states')['REGISTER_PUSH']:
                        push_set = False

                        if data['text'] == file_system.read('keyboards')['REGISTER_PUSH']['buttons'][0][0][0]:
                            push_set = True
                            file_system.update_user(str(data['from_id']), 'push',
                                                    file_system.read('states')['PUSH_STANDARD'])

                        elif data['text'] == file_system.read('keyboards')['REGISTER_PUSH']['buttons'][1][0][0]:
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

                        # Todo: создать остальную часть меню

                else:
                    file_system.log('users', 'Зарегистрирован ID ' + str(data['from_id']))
                    file_system.new_user(str(data['from_id']))
                    self.send_keyboard(
                        data['from_id'],
                        "REGISTER_CLASS",
                        file_system.read('messages').get('REGISTER_GREETING')
                    )
