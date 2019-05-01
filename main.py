from flask import Flask, request
import json
from questions_file import QUESTIONS, STATISTICS_QUESTIONS, Entries, WRONG_NAME, START_GAME, UNDERSTAND_START_GAME, WITHOUT_PROMPT, TIME_ENDED, GOOD_ANSWER, GAME_OVER

import random

USERS = dict()



app = Flask(__name__)
OK_WORDS = ['да', 'ладно', 'хорошо', 'давайте', 'давай', 'начинаем', 'ок', 'ok', 'окей']
BAD_WORDS= ['не хочу', 'не надо', 'без подсказок', 'без', 'отказываюсь', 'не нужна']
STOP_WORDS = ['стоп', 'считаем очки', 'фиксируем прибыль']
TOP_LIST_WORDS = ['топ-лист', 'топ лист', 'список топ', 'топ игроков']
RESTART_WORDS = ['игру сначала', 'начать игру сначала', 'заного', 'рестарт', 'ещё попытку']

string_variant = 'абвг'


TOPLIST = []


@app.route('/post', methods=['POST'])
def main():
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(response, request.json)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = random.choice(Entries)
        USERS[user_id] = dict()
        USERS[user_id]['name'] = None
        return

    if USERS[user_id]['name'] is None:
        name = get_name(req)
        if name is None:
            res['response']['text'] = random.choice(WRONG_NAME)

            return

        name = name[0].upper() + name[1:].lower()
        USERS[user_id]['name'] = name
        res['response']['text'] = \
            random.choice(START_GAME).format(name)

        res['response']['buttons'] = []

        res['response']['buttons'].append(
            {
                'title': 'Да',
                'hide': True
            }
        )
        USERS[user_id]['game_status'] = 0

        res['response']['buttons'].append(
            {
                'title': 'Узнать правила',
                'hide': True
            }
        )

        arr = []
        for i in QUESTIONS:
            arr.append(i)

        random.shuffle(arr)
        USERS[user_id]['list_of_questions'] = arr
        return


    user_words = req['request']['nlu']['tokens']
    user_proposition = req['request']['original_utterance'].lower().replace('  ', ' ')


    if 'правила' in user_proposition or 'узнать правила' in user_proposition:
        tt = 'Правила очень простые! За каждый верный ваш ответ вам начисляются очки! ' \
        'После неправильного ответа на вопрос все накопленные вами очки сгорают. ' \
        'В любой момент игры вы можете сказать "Стоп" и мы сохраним ваш результат в топ-лист нашей игры. ' \
        'Ну что же, начнём?'
        res['response']['text'] = tt
        res['response']['buttons'] = []

        res['response']['buttons'].append(
            {
                'title': 'Да',
                'hide': True
            }
        )
        return


    if USERS[user_id]['game_status'] == 0:
        flag = False
        for word in OK_WORDS:
            if word in user_words:
                flag = True
                break

        if not flag:
            res['response']['text'] = \
                random.choice(UNDERSTAND_START_GAME).format(USERS[user_id]['name'])
            return

        USERS[user_id]['question_number'] = 1
        QUEST = get_question(1, user_id)
        USERS[user_id]['count_correct_answers'] = 0
        USERS[user_id]['question_status'] = 1
        USERS[user_id]['question_data'] = QUEST
        USERS[user_id]['points'] = 0
        USERS[user_id]['game_status'] = 1
        USERS[user_id]['tips'] = {
        '50 на 50': 'Остаётся два варианта ответа, один из который правильный',
        'Доп. жизнь': 'В текущем вопросе вам даётся право на ошибку',
        'Звонок другу': 'Помощь от друга',
        'Помощь зала': 'Зрители голосуют за понравившиеся им варианты ответов'
    }
        give_question(res, user_id)
        return


    if USERS[user_id]['game_status'] == 3:
        flag = False
        for w in BAD_WORDS:
            if w in user_proposition:
               flag = True
               break

        if flag:
            USERS[user_id]['game_status'] = 1
            give_question(res, user_id)
            res['response']['text'] = random.choice(WITHOUT_PROMPT)
            return

        if 'доп. жизнь' in user_proposition or 'дополнительная жизнь' in user_proposition or 'доп.жизнь' in user_proposition:
            USERS[user_id]['game_status'] = 1

            if 'Доп. жизнь' not in USERS[user_id]['tips']:
                give_question(res, user_id)

                res['response']['text'] = 'Увы, но вы уже использовали этот бонус! Выберите ответ.'
                return
            USERS[user_id]['question_status'] = 2
            USERS[user_id]['tips'].pop('Доп. жизнь')
            give_question(res, user_id)
            res['response']['text'] = 'Бонус активирован! У вас есть право ошибиться на текущем вопросе!'
            return

        if '50 на 50' in user_proposition:
            USERS[user_id]['game_status'] = 1
            if '50 на 50' not in USERS[user_id]['tips']:
                give_question(res, user_id)
                res['response']['text'] = 'Увы, но вы уже использовали этот бонус! Выберите ответ.'
                return

            arr = []
            for maybe in USERS[user_id]['question_data']['possible_answers']:
                if maybe.upper() != USERS[user_id]['question_data']['correct_answer'].upper():
                    arr.append(maybe)

            random.shuffle(arr)
            while len(arr) > 1:
                USERS[user_id]['question_data']['possible_answers'].pop(arr[0])
                del arr[0]

            USERS[user_id]['tips'].pop('50 на 50')
            give_question(res, user_id)
            res['response']['text'] = 'Мы убрали лишние ответы! Делайте выбор!'
            return



        if 'звонок дру' in user_proposition or 'другу звон' in user_proposition or 'позвоню дру' in user_proposition:
            USERS[user_id]['game_status'] = 1
            if 'Звонок другу' not in USERS[user_id]['tips']:
                give_question(res, user_id)
                res['response']['text'] = 'Вы уже использовали этот бонус! Выберите ответ.'
                return

            USERS[user_id]['tips'].pop('Звонок другу')
            arr = []
            for g in USERS[user_id]['question_data']['possible_answers']:
                arr.append(g)

            give_question(res, user_id)
            res['response']['text'] = USERS[user_id]['question_data']['call_friend'].format(random.choice(arr))
            res['response']['text'] += random.choice(TIME_ENDED)
            return


        if 'помощь зала' in user_proposition or 'зал помоги' in user_proposition:
            USERS[user_id]['game_status'] = 1
            if 'Помощь зала' not in USERS[user_id]['tips']:
                give_question(res, user_id)
                res['response']['text'] = 'Вы уже использовали эту подсказку! Пора выбирать ответ.'
                return

            USERS[user_id]['tips'].pop('Помощь зала')
            text = 'Зрители берут в руки пульты и голосую!..\n Голосование закончилось!\n Результаты следующие:\n'
            cnt = 0
            for w in USERS[user_id]['question_data']['possible_answers']:
                cnt += get_statistics(USERS[user_id]['question_data']['id'])[w]

            for w in USERS[user_id]['question_data']['possible_answers']:
                text += w + ' - ' + str(int(100 * get_statistics(USERS[user_id]['question_data']['id'])[w] / cnt)) + '%\n'

            give_question(res, user_id)
            res['response']['text'] = text + '\nАнализируйте и делайте ваш выбор!'
            return

    elif USERS[user_id]['game_status'] == 1:
        flag2 = False
        for stop in STOP_WORDS:
            if stop in user_proposition:
                flag2 = True
                break

        if flag2:
            USERS[user_id]['game_status'] = 4
            res['response']['text'] = '{}, вы набрали {} очков! Под каким именем вас записать в топ-лист?'.format(USERS[user_id]['name'], USERS[user_id]['points'])
            return

        for w in user_words:
            if len(w) == 1 and w.lower() in string_variant.lower():
                if w.lower() in USERS[user_id]['question_data']['correct_answer'].lower():
                    player_give_correct_answer(res, user_id)
                    return
                else:
                    give_wrong_answer(res, user_id, w.upper())
                    return


        if 'подсказка' in user_proposition:
            if len(USERS[user_id]['tips']) == 0:
                give_question(res, user_id)
                res['response']['text'] = 'Увы, но у вас кончились подсказки.'
                return

            res['response']['text'] = 'Вам доступны следующие подсказки:\n'
            res['response']['buttons'] = []

            for t in USERS[user_id]['tips']:
                res['response']['text'] += t + ' - ' +  USERS[user_id]['tips'][t] + '\n'
                res['response']['buttons'].append(
                    {
                        'title': t,
                        'hide': True
                    }
                )

            res['response']['buttons'].append(
                {
                    'title': 'Не нужна',
                    'hide': True
                }
            )
            USERS[user_id]['game_status'] = 3
            return

        else: # Ответ от игрока не получен
            give_question(res, user_id)
            res['response']['text'] = 'Я не поняла ваш ответ, для используйте только буквы:\n А, Б, В или Г.'
            return

    elif USERS[user_id]['game_status'] == 4:
        USERS[user_id]['game_status'] = 6
        nickname = req['request']['original_utterance'].strip().replace('  ', ' ')
        points = USERS[user_id]['points']
        myind = 1
        for i in range(len(TOPLIST)):
            if TOPLIST[i][0] > points:
                myind += 1
        TOPLIST.append((points, nickname))
        res['response']['text'] = 'Вы занимаете {} место! Я записала вас под никнэймом - {}!\n' \
                                  'Вы хотите начать игру сначала? Или может быть посмотреть топ игроков?' \
                                  ''.format(myind, nickname)
        res['response']['buttons'] = []

        USERS[user_id]['game_status'] = 6

        res['response']['buttons'].append(
            {
                'title': 'Посмотреть топ-лист',
                'hide': True
            }
        )

        res['response']['buttons'].append(
            {
                'title': 'Начать игру сначала',
                'hide': True
            }
        )
        return

    elif USERS[user_id]['game_status'] == 5:
        USERS[user_id]['game_status'] = 6
        res['response']['text'] = 'Вы хотите начать игру сначала? Или может быть посмотреть топ игроков?'
        res['response']['buttons'] = []

        res['response']['buttons'].append(
            {
                'title': 'Посмотреть топ-лист',
                'hide': True
            }
        )

        res['response']['buttons'].append(
            {
                'title': 'Начать игру сначала',
                'hide': True
            }
        )
        return

    elif USERS[user_id]['game_status'] == 6:
        top_flag = False
        for w in TOP_LIST_WORDS:
            if w in user_proposition:
                top_flag = True
                break

        res['response']['buttons'] = []

        res['response']['buttons'].append(
            {
                'title': 'Посмотреть топ-лист',
                'hide': True
            }
        )

        res['response']['buttons'].append(
            {
                'title': 'Начать игру сначала',
                'hide': True
            }
        )


        top = ''
        TOPLIST.sort(reverse=True)
        if top_flag:
            for i in range(min(len(TOPLIST), 10)):
                top += str(i + 1) + ') ' + TOPLIST[i][1] + ' - ' + str(TOPLIST[i][0]) + '\n'

            res['response']['text'] = 'Топ игроков на текущее время\n' + top
            return

        flag_restart = False
        for w in RESTART_WORDS:
            if w in user_proposition:
                flag_restart = True
                break


        if flag_restart:
            if(len(USERS[user_id]['list_of_questions']) == 0):
                res['response']['text'] = \
                    '{}, у нас кончились вопросы для вас! Ждём вас в следующий раз у нас в гостях, когда у нас пополнятся вопросы!'.format(USERS[user_id]['name'])
                USERS[user_id]['game_status'] = 6
                res['response']['buttons'] = []
                res['response']['buttons'].append(
                    {
                        'title': 'Посмотреть топ-лист',
                        'hide': True
                    }
                )
                return

            res['response']['text'] = \
                'Итак, {}, вы готовы начать игру?'.format(USERS[user_id]['name'])

            USERS[user_id]['game_status'] = 0

            res['response']['buttons'] = []
            res['response']['buttons'].append(
                {
                    'title': 'Да',
                    'hide': True
                }
            )

            return

        res['response']['text'] = \
            '{}, я не совсем поняла вас.'.format(USERS[user_id]['name'])
        return



def get_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            if ('first_name' in entity['value']):
                return entity['value']['first_name']
            return None



def get_question(level, user_id):
    if(len(USERS[user_id]['list_of_questions']) == 0):
        return None
    need_id = USERS[user_id]['list_of_questions'][0]
    return  QUESTIONS[need_id]



def give_question(res, user_id):
    if(len(USERS[user_id]['list_of_questions']) == 0):
        res['response']['text'] = 'У нас кончились вопросы для вас! Ждём вас в следующий раз у нас в гостях, когда у нас пополнятся вопросы!'
        USERS[user_id]['game_status'] = 5
        return



    res['response']['text'] = 'Вопрос №{}'.format( USERS[user_id]['question_number'] ) + ', стоимость вопроса: {} очков!\n'.format(USERS[user_id]['question_data']['cost']) \
                              + USERS[user_id]['question_data']['text'] + ' \n'

    res['response']['buttons'] = []

    for w in string_variant.upper():
        if w not in USERS[user_id]['question_data']['possible_answers']:
            continue

        res['response']['buttons'].append(
            {
            'title': w,
            'hide': True
        }
        )

        res['response']['text'] += w.upper() + ') ' + USERS[user_id]['question_data']['possible_answers'][w] + '\n'

    res['response']['buttons'].append({
        'title': 'Подсказка',
        'hide': True
    })

    res['response']['buttons'].append({
        'title': 'Стоп',
        'hide': True
    })

    return

def player_give_correct_answer(res, user_id):
    del USERS[user_id]['list_of_questions'][0]
    STATISTICS_QUESTIONS[USERS[user_id]['question_data']['id']][USERS[user_id]['question_data']['correct_answer']] += 1
    USERS[user_id]['points'] += USERS[user_id]['question_data']['cost']
    USERS[user_id]['question_number'] += 1
    USERS[user_id]['count_correct_answers'] += 1
    USERS[user_id]['question_status'] = 1
    NEW_QUEST = get_question(USERS[user_id]['question_number'], user_id)
    if(NEW_QUEST is None):
        res['response']['text'] = 'И это правильный ответ! Теперь у вас {} очков!\n К сожалению, у нас кончились для вас вопросы. ' \
                                  ''.format(USERS[user_id]['points']) + '\n Под каким именем вас записать в топ-лист?'
        USERS[user_id]['game_status'] = 4
        return

    USERS[user_id]['question_data'] = NEW_QUEST
    give_question(res, user_id)
    res['response']['text'] = random.choice(GOOD_ANSWER) + ' Теперь у вас {} очков!\n'.format(USERS[user_id]['points']) + res['response']['text']
    return




def give_wrong_answer(res, user_id, myans):
    STATISTICS_QUESTIONS[USERS[user_id]['question_data']['id']][myans] += 1

    if USERS[user_id]['question_status'] == 2:
        if myans in USERS[user_id]['question_data']['possible_answers']:
            USERS[user_id]['question_data']['possible_answers'].pop(myans.upper())

        give_question(res, user_id)
        USERS[user_id]['question_status'] = 1

        res['response']['text'] = 'Увы, но это неверный ответ, но у вас есть ещё одна попытка!'
        return

    res['response']['buttons'] = []
    res['response']['text'] = random.choice(GAME_OVER)
    del USERS[user_id]['list_of_questions'][0]
    res['response']['buttons'].append({
        'title': 'Что дальше?',
        'hide': True
    })

    USERS[user_id]['game_status'] = 5
    return


def get_statistics(id_quest):
    return STATISTICS_QUESTIONS[id_quest]


if __name__ =='__main__':
    app.run()



