# запускать этот файл, для работы бота

import vk_messaging


def cycle():
    try:
        server = vk_messaging.Server()
        server.start()
        
    except:
        cycle()


cycle()
