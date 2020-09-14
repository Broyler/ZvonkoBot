from const import settings, color_values
from utils import file_system

from random import randint
from sys import exit

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

        keyboard = VkKeyboard(one_time=False)
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

    # Todo: сделать функцию на сегодняшнее расписание

    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                data = event.object.get('message')

                if data['text'] == 'admin:stop_bot' and data['from_id'] in file_system.read('admins'):
                    print('[exit] Администратор ' + str(data['from_id']) + ' остановил работу бота.')
                    exit(0)

                elif data['text'] == 'admin:reset_users' and data['from_id'] in file_system.read('admins'):
                    print('[log] Администратор ' + str(data['from_id']) + ' сбросил пользователей.')
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
                        # Todo: создать обработчик быстрого меню
                        pass

                else:
                    file_system.new_user(str(data['from_id']))
                    self.send_keyboard(
                        data['from_id'],
                        "REGISTER_CLASS",
                        file_system.read('messages').get('REGISTER_GREETING')
                    )
