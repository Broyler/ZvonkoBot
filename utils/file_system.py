from json import loads, dumps


def read(filename):
    try:
        with open('json/'+filename+'.json', 'r', encoding='utf-8') as file:
            return loads(file.read())

    except FileNotFoundError:
        log('log', '[error] Файл ' + filename + ' не найден (код 5)')
        return None


def write(filename, value):
    try:
        with open('json/'+filename+'.json', 'w', encoding='utf-8') as file:
            file.write(dumps(value))

    except KeyError:
        log('log', '[error] Ключ не найден (код 4)')
        return None

    else:
        return 0


def add_junk(value):
    try:
        file = list(read('junk'))
        file.append(str(value))
        write('junk', file)

    except FileNotFoundError:
        log('log', '[error] Ошибка, файл не найден')


def new_user(user_id):
    try:
        users = read('vk_users')
        users[user_id] = {
            "state": read('states').get('REGISTER_BUILDING'),
            "table": False,
            "class": 8,
            "letter": "а",
            "push": [1, 1, 1, 1, 2],
            "coins": 10
        }
        write('vk_users', users)

    except KeyError:
        log('log', '[error] Ключ не найден (код 3)')
        return None

    else:
        return 0


def update_user(user_id, field, value):
    try:
        users = read('vk_users')
        users[user_id][field] = value
        write('vk_users', users)

    except KeyError:
        log('log', '[error] Ключ не найден (код 2)')
        return None

    else:
        return 0


def log(filename, message):
    try:
        with open('logs/' + filename + '.txt', 'a', encoding='utf-8') as file:
            file.write(message + '\n')

    except FileNotFoundError:
        print('Файл не найден (код 1)')
        return None

    else:
        return 0
