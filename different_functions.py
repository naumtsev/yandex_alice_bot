import json



def save_users():
    f = open('users.txt', 'w')
    json.dump(USERS, f)
    f.close()


def get_USERS():
    global USERS
    f = open('users.txt', 'r')
    USERS = json.loads(f.read())
    f.close()






def get_name(req):
    user_proposition = req['request']['original_utterance'].lower().replace('  ', ' ')
    if 'аноним' in user_proposition:
        return 'Аноним'

    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            if ('first_name' in entity['value']):
                return entity['value']['first_name']
            return None