from utils import file_system, tools
import vk_messaging

from datetime import datetime
from time import sleep
from random import choice


time_count = 0


while True:
    try:
        users = file_system.read('vk_users')

    except:
        continue

    dt = datetime.now()

    if tools.temp() >= 70:
        for admin in file_system.read('admins'):
            vk_messaging.Server().send(admin, 'Critical temp: ' + str(tools.temp()) + '°C')

    if time_count >= 960:
        vk_messaging.Server().delete_junk()
        time_count = 0

    current_date = tools.date(str(dt.day) + '.' + str(dt.month))
    current_day = current_date.split('.')[0]
    current_month = current_date.split('.')[1]
    flag = False

    for holiday in file_system.read('holidays'):
        holiday[0] = tools.date(holiday[0])
        holiday[1] = tools.date(holiday[1])

        start_day = holiday[0].split('.')[0]
        start_month = holiday[0].split('.')[1]

        end_day = holiday[1].split('.')[0]
        end_month = holiday[1].split('.')[1]

        if start_month <= current_month <= end_month and start_day <= current_day < end_day:
            flag = True

        else:
            flag = False

    if not flag:
        for user_id in users:
            try:
                user = users[user_id]

                if user['state'] != 20 and user['state'] != 21 and user['state'] != 22 and user['state'] != \
                        file_system.read('states').get('REGISTER_BUILDING'):
                    if not user['table'] or file_system.read('calls')[str(user['class'])]['from_lesson'][len(
                            file_system.read('table')
                            [str(user['class'])][user['letter']]
                            [dt.weekday()])-1] \
                            >= tools.time(str(dt.hour) + ':' + str(dt.minute)):
                        if user['push'][0] == 1:
                            minute = dt.minute + user['push'][4]
                            hour = dt.hour

                            if minute >= 60:
                                hour += 1
                                minute -= 60

                            time = str(hour) + ':' + str(minute)

                            for call in file_system.read('calls')[str(user['class'])]['to_lesson']:
                                if call == time:
                                    if user['push'][3] == 0:
                                        msg = vk_messaging.Server().send(user_id, choice(
                                            file_system.read('messages')['TO_LESSON']))
                                        file_system.add_junk(str(msg))

                                    else:
                                        msg = vk_messaging.Server().send_lesson_next(user_id)
                                        file_system.add_junk(str(msg))

                                    break

                        if user['push'][1] == 1:
                            minute = dt.minute
                            hour = dt.hour
                            time = str(hour) + ':' + str(minute)

                            for call in file_system.read('calls')[str(user['class'])]['to_lesson']:
                                if call == time:
                                    msg = vk_messaging.Server().send(
                                        user_id, choice(file_system.read('messages')['TO_LESSON']))
                                    file_system.add_junk(str(msg))
                                    break

                        if user['push'][2] == 1:
                            minute = dt.minute
                            hour = dt.hour
                            time = str(hour) + ':' + str(minute)

                            for call in file_system.read('calls')[str(user['class'])]['from_lesson']:
                                if call == time:
                                    if call == file_system.read('calls')[str(user['class'])]['from_lesson'][-1]:
                                        msg = vk_messaging.Server().send(user_id,
                                                                         file_system.read('messages')['ENDLESSON'])

                                    else:
                                        text = choice(file_system.read('messages')['FROM_LESSON']) + ' ' + \
                                               vk_messaging.Server().get_lesson_next(user_id)
                                        msg = vk_messaging.Server().send(
                                            user_id,
                                            text)
                                    file_system.add_junk(str(msg))
                                    break

            except:
                print('error', user)

    sleep(60)
    time_count += 1
