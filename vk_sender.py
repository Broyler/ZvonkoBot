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

    for user_id in users:
        try:
            user = users[user_id]

            if user['state'] != 20 and user['state'] != 21 and user['state'] != 22 and user['state'] != \
                    file_system.read('states').get('REGISTER_BUILDING'):
                if not user['table'] or file_system.read('calls')[str(user['class'])]['from_lesson'][len(
                        file_system.read('table')
                        [str(user['class'])][user['letter']]
                        [dt.weekday()])-1] \
                        >= str(dt.hour) + ':' + str(dt.minute):
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
                                msg = vk_messaging.Server().send(user_id,
                                                                 choice(file_system.read('messages')['FROM_LESSON']))
                                file_system.add_junk(str(msg))
                                break
                            
        except:
            print('error', user)

    sleep(60)
    time_count += 1
