from json import loads, dumps


def read(filename):
    try:
        with open('json/'+filename+'.json', 'r', encoding='utf-8') as file:
            return loads(file.read())

    except FileNotFoundError:
        print('[error] No such file or directory: ' + filename)
        return None


def write(filename, value):
    try:
        with open('json/'+filename+'.json', 'w', encoding='utf-8') as file:
            file.write(dumps(value))

    except ValueError:
        print('[error] Value is incorrect')
        return None

    else:
        return 0


def new_user(user_id):
    try:
        users = read('vk_users')
        users[user_id] = {
            "state": read('states').get('REGISTER_CLASS'),
            "class": 8,
            "letter": "а",
            "push": [1, 0, 0, 0, 2]
        }
        write('vk_users', users)

    except IndexError:
        print('[error] Invalid element index')
        return None

    else:
        return 0


def update_user(user_id, field, value):
    try:
        users = read('vk_users')
        users[user_id][field] = value
        write('vk_users', users)

    except IndexError:
        print('[error] Invalid element index')
        return None

    else:
        return 0
