#!/usr/bin/python
# -*- coding: utf-8 -*-
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, SelectField
from wtforms.widgets import TextArea, TextInput
from wtforms.validators import DataRequired, Email

from flask import Flask, request, render_template, redirect
import json
import random
from different_functions import *
from DIFFERENT_TEXT import *
from database_cfg import *

image_id = '1533899/eab11fdf307e25539201'


USERS = dict()
TOPLIST = []


def save_toplist():
    f = open('toplist.txt', 'w')
    json.dump(TOPLIST, f)
    f.close()

def get_TOPLIST():
    global TOPLIST
    f = open('toplist.txt', 'r')
    TOPLIST = json.loads(f.read())
    f.close()


get_TOPLIST()

app = Flask(__name__)


OK_WORDS = ['да', 'ладно', 'хорошо', 'давайте', 'давай', 'начинаем', 'ок', 'ok', 'окей']
BAD_WORDS= ['не хочу', 'не надо', 'без подсказок', 'без', 'отказываюсь', 'не нужна']
STOP_WORDS = ['стоп', 'считаем очки', 'фиксируем прибыль']
TOP_LIST_WORDS = ['топ-лист', 'топ лист', 'список топ', 'топ игроков', 'топ']
RESTART_WORDS = ['игру сначала', 'начать игру сначала', 'заного', 'рестарт', 'ещё попытку', 'попытк']


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
    user_words = req['request']['nlu']['tokens']
    user_proposition = req['request']['original_utterance'].lower().replace('  ', ' ')

    if 'что ты умеешь' in user_proposition or ('помощь' in user_proposition and 'зал' not in user_proposition):
        what_i_can_do(res, req, user_id)
        return

    if req['session']['new']:
        give_info_new_user(res, user_id)
        return

    if user_id not in USERS:
        give_info_new_user(res, user_id)
        return

    if USERS[user_id]['name'] is None:
        user_give_her_name(user_id, res, req)
        return

    if USERS[user_id]['game_status'] == 1:
        user_choose_category(res, req, user_id)
        return

    if USERS[user_id]['game_status'] == 2:
        check_user_answer(res, req, user_id)
        return

    if USERS[user_id]['game_status'] == 3:
        add_new_top_player(res, req, user_id)
        return

    if USERS[user_id]['game_status'] == 4:
        if 'что дальше' not in  user_proposition:
            res['response']['text'] = 'Простите, но я вас не поняла!\n'
            res['response']['buttons'] = []
            res['response']['buttons'].append({
                'title': 'Что дальше?',
                'hide': True
            })
            return
        what_the_next(res, req, user_id)
        return

    if USERS[user_id]['game_status'] == 5:
        change_category_or_toplist(res, req, user_id)
        return

    if  USERS[user_id]['game_status'] == 6:
        check_for_user_give_tip(res, req, user_id)
        return






def user_give_her_name(user_id, res, req):
    name = get_name(req)
    if name is None:
        res['response']['text'] = random.choice(WRONG_NAME)
        return

    name = name[0].upper() + name[1:].lower()
    USERS[user_id]['name'] = name
    ALL = []
    for id_category in categories:
        if id_category in USERS[user_id]:
            continue
        else:
            BUFF = get_list_question(id_category)
            random.shuffle(BUFF)
            USERS[user_id][id_category] = BUFF
            ALL += USERS[user_id][id_category]

    #Супер-викторина
    random.shuffle(ALL)
    USERS[user_id]['7'] = ALL

    give_categories(res, user_id)
    res['response']['text'] = random.choice(CHOOSE_CATEGORY).format(USERS[user_id]['name']) + '\n' + res['response']['text']
    USERS[user_id]['game_status'] = 1
    return



def what_i_can_do(res, req, user_id):
    text_ = FULL_HELP_INFO


    if USERS[user_id]['name'] is None:
        text_ += "Представьтесь, пожалуйста!"
        res['response']['buttons'] = []

        res['response']['buttons'].append(
            {
                'title': 'Аноним',
                'hide': True
            })
    elif USERS[user_id]['game_status'] == 1:
        text_ += "Пора выбрать категорию!"
        give_categories(res, user_id)
    elif USERS[user_id]['game_status'] == 2:
        text_ += "Пора выбирать правильный ответ!"
        give_question_buttons(res, user_id)
    elif USERS[user_id]['game_status'] == 4:
        text_ += "Что вы хотите делать дальше?"
        give_change_or_toplist_buttons(res, user_id)

        USERS[user_id]['game_status'] = 5

    elif USERS[user_id]['game_status'] == 6:
        text_ += "Пора выбрать подсказку, которую вы хотите использовать!"
        give_hint(res, req, user_id)

    res['response']['text'] = text_
    return




def give_info_new_user(res, user_id):
    res['response']['card'] = {}
    res['response']['card']['type'] = 'BigImage'
    res['response']['card'][
        'description'] = 'Добро пожаловать в игру "Интеллектуальный Олимп"! Здесь я задаю вам вопросы и к ним даю четыре возможных варианта ответа. Перед началом игры представьтесь, пожалуйста.'
    res['response']['card']['image_id'] = image_id
    res['response'][
        'text'] = 'Добро пожаловать в игру "Интеллектуальный Олимп"! Здесь я задаю вам вопросы и даю 4 варианта ответа к ним. За каждый верный ответ вы получаете определённое количество очков. Ответив неверно, ваши очки сгорают. Чтобы сохранить свой результат скажите "Стоп" в любой момент времени. Перед началом игры представьтесь, пожалуйста.'
    res['response']['buttons'] = []

    res['response']['buttons'].append(
        {
        'title': 'Аноним',
        'hide': True
        })


    USERS[user_id] = dict()
    USERS[user_id]['name'] = None
    return


def user_choose_category(res, req, user_id):
    user_words = req['request']['nlu']['tokens']
    user_proposition = req['request']['original_utterance'].lower().replace('  ', ' ')

    USER_CATEGORY = None

    for id_category in categories:
        if categories[id_category].lower() in user_proposition:
            USER_CATEGORY = id_category
            break

    if USER_CATEGORY is None:
        give_categories(res, user_id)
        res['response']['text'] = BAD_CHANGE_CATEGORY + res['response']['text']
        return


    USERS[user_id]['category'] = USER_CATEGORY
    USERS[user_id]['points'] = 0
    QUEST = get_question(res, user_id)

    if QUEST is None:
        give_categories(res, user_id)
        res['response']['text'] = 'Увы, но у нас для вас нет вопросов из данной категории, выберите другую категорию.'
        return

    USERS[user_id]['question'] = QUEST
    USERS[user_id]['round'] = 1
    USERS[user_id]['count_wrong'] = 0
    give_question(res, user_id)

    res['response']['text'] = 'Итак, вы выбрали категорию "{}"!\n'.format(categories[USER_CATEGORY]) +  get_text_question(user_id)


    give_question_buttons(res, user_id)
    USERS[user_id]['game_status'] = 2

    USERS[user_id]['tips'] = {
                                'Доп. жизнь': 'В текущем вопросе вам даётся право на ошибку',
                                '50 на 50': 'Остаётся два варианта ответа, один из который правильный',
                                'Звонок другу': 'Помощь друга',
                                'Помощь зала': 'Зрители голосуют за понравившиеся им варианты ответов'
                            }
    return


def get_question(res, user_id):
    my_category = USERS[user_id]['category']
    if len(USERS[user_id][my_category]) == 0:
        return None

    USERS[user_id]['question'] = get_data_question(USERS[user_id][my_category][0])
    del USERS[user_id][my_category][0]
    return USERS[user_id]['question']


def get_data_question(id_question):
    QUEST = QUESTIONS.get(id_question)
    question_dict = dict()


    question_dict['id'] = id_question
    question_dict['category'] = QUEST[1]
    question_dict['text_question'] = QUEST[2]

    question_dict['possible'] = dict()
    question_dict['possible']['А'] = QUEST[3]
    question_dict['possible']['Б'] = QUEST[4]
    question_dict['possible']['В'] = QUEST[5]
    question_dict['possible']['Г'] = QUEST[6]

    question_dict['statistics'] = dict()
    question_dict['statistics']['А'] = QUEST[7]
    question_dict['statistics']['Б'] = QUEST[8]
    question_dict['statistics']['В'] = QUEST[9]
    question_dict['statistics']['Г'] = QUEST[10]

    question_dict['call_friend'] = QUEST[11]
    question_dict['correct_answer'] = QUEST[12]
    question_dict['level'] = QUEST[13]
    question_dict['points'] = QUEST[14]
    return question_dict



def give_categories(res, user_id):
    res['response']['buttons'] = []
    res['response']['text'] = ''

    for id in categories:
        res['response']['buttons'].append({
            'title': categories[id],
            'hide': True
        })
        res['response']['text'] += categories[id] + '\n'
    return


def give_question(res, user_id):
    var = 'АБВГ'
    give_question_buttons(res, user_id)
    res['response']['text'] = get_text_question(user_id)

    return


def check_user_have_question_in_category(user_id, category):
    return len(USERS[user_id][category]) != 0

def get_list_question(id_category):
    arr = []
    for i in QUESTIONS.get_all_by_category(id_category):
        arr.append(i[0])
    return arr




string_variant = 'АБВГ'

def check_user_answer(res, req, user_id):
    user_words = req['request']['nlu']['tokens']
    user_proposition = req['request']['original_utterance'].lower().replace('  ', ' ')

    flag = False

    for w in STOP_WORDS:
        if w in user_proposition:
            flag = True
            break

    if flag:
        give_result_and_ask_nickname(res, user_id)
        return

    if 'подсказк' in user_proposition or 'подскаж' in user_proposition:
        give_hint(res, req, user_id)
        return

    for w in user_words:
        if len(w) == 1 and w.lower() in string_variant.lower():
            if w.lower() in USERS[user_id]['question']['correct_answer'].lower():
                player_give_correct_answer(res, user_id, w.lower())
                return
            else:
                player_give_wrong_answer(res, user_id, w.upper())
                return

    res['response']['text'] = 'Простите, я не поняла ваш ответ, для ответа используйте буквы: А, Б, В или Г.'
    give_question_buttons(res, user_id)
    return


def player_give_correct_answer(res, user_id, w):
    update_statistics(USERS[user_id]['question']['id'], w, 1)
    USERS[user_id]['points'] += USERS[user_id]['question']['points']
    NEW_QUEST = get_question(res, user_id)
    USERS[user_id]['count_wrong'] = 0

    if NEW_QUEST is None: # Кончились вопросы
        res['response']['text'] \
            = 'И это правильный ответ! Теперь у вас {} очков!\n К сожалению, у нас кончились для вас вопросы. ' \
                          ''.format(USERS[user_id]['points']) + '\n Под каким именем вас записать в топ-лист?'
        USERS[user_id]['game_status'] = 3
        return

    USERS[user_id]['round'] += 1
    res['response']['text'] = random.choice(GOOD_ANSWER) + ' Теперь у вас {} очков!\n'.format(
        USERS[user_id]['points']) + get_text_question(user_id)

    USERS[user_id]['game_status'] = 2

    USERS[user_id]['question'] = NEW_QUEST
    give_question_buttons(res, user_id)


def player_give_wrong_answer(res, user_id, w):
    update_statistics(USERS[user_id]['question']['id'], w, 1)
    if USERS[user_id]['count_wrong']:
        if w in USERS[user_id]['question']['possible']:
            USERS[user_id]['question']['possible'].pop(w.upper())
        USERS[user_id]['count_wrong'] = 0
        res['response']['text'] = WE_HAVENT_QUESTION_IN_THIS_CATEGORY
        give_question_buttons(res, user_id)
        return

    res['response']['text'] = random.choice(GAME_OVER)
    res['response']['buttons'] = []
    res['response']['buttons'].append({
        'title': 'Что дальше?',
        'hide': True
    })
    USERS[user_id]['game_status'] = 4
    return



def get_text_question(user_id):
    text_ = 'Вопрос №{}'.format(
        USERS[user_id]['round']) + ', стоимость вопроса: {} очков!'.format(
        USERS[user_id]['question']['points']) + '\n' + str(USERS[user_id]['question']['text_question']) + '\n'
    for w in string_variant:
        if w in USERS[user_id]['question']['possible']:
            text_ += str(w) + ') ' + str(USERS[user_id]['question']['possible'][w]) + '\n'

    return text_

def give_question_buttons(res, user_id):
    res['response']['buttons'] = []
    for w in string_variant.upper():
        if w in USERS[user_id]['question']['possible']:
            res['response']['buttons'].append(
                {
                    'title': w,
                    'hide': True
                }
            )

    res['response']['buttons'].append(
        {
            'title': 'Стоп',
            'hide': True
        }
    )

    res['response']['buttons'].append(
        {
            'title': 'Подсказка',
            'hide': True
        }
    )
    res['response']['buttons'].append(
        {
            'title': 'Помощь',
            'hide': True
        }
    )


def add_new_top_player(res, req, user_id):
    global TOPLIST
    nickname = req['request']['original_utterance'].strip().replace('  ', ' ')[:20]
    points = USERS[user_id]['points']
    myind = 1
    flag_now = False
    for i in range(len(TOPLIST)):
        if TOPLIST[i][0] < points:
            TOPLIST.insert(i, [points, nickname])
            myind = i + 1
            flag_now = True
            break

    res['response']['buttons'] = []
    res['response']['buttons'].append({
        'title': 'Что дальше?',
        'hide': True
    })

    if not flag_now:
        TOPLIST.insert(len(TOPLIST), [points, nickname])
        myind = len(TOPLIST)

    save_toplist()

    res['response']['text'] = 'Вы занимаете {} место! Я записала вас под никнэймом - {}!'.format(myind, nickname)
    USERS[user_id]['game_status'] = 4
    return



def what_the_next(res, req, user_id):
    text_ = 'Вы хотите начать новую игру в другой категории, остаться в текущей, или может быть посмотреть топ-лист?'
    USERS[user_id]['game_status'] = 5
    res['response']['text'] = text_
    res['response']['buttons'] = []

    give_change_or_toplist_buttons(res, user_id)

    return

def change_category_or_toplist(res, req, user_id):
    user_words = req['request']['nlu']['tokens']
    user_proposition = req['request']['original_utterance'].lower().replace('  ', ' ')


    flag = False
    for w in CHANGE_CATEGORY_WORDS:
        if w in user_proposition:
            flag = True
            break


    if flag:
        give_categories(res, user_id)
        res['response']['text'] = random.choice(CHOOSE_CATEGORY).format(USERS[user_id]['name']) + '\n' + \
                                  res['response']['text']
        USERS[user_id]['game_status'] = 1
        return




    flag = False
    for w in STAY_AT_THIS_CATEGORY:
        if w in user_proposition:
            flag = True
            break

    if flag:
        now_category = USERS[user_id]['category']
        if len(USERS[user_id][now_category]) == 0:
            text_ = 'Увы, но в текущей категории кончились вопросы для вас.'
            res['response']['text'] = text_
            give_change_or_toplist_buttons(res, user_id)

            return



        USERS[user_id]['game_status'] = 2
        USERS[user_id]['round'] = 1
        USERS[user_id]['points'] = 0
        USERS[user_id]['count_wrong'] = 0

        USERS[user_id]['question'] = get_question(res, user_id)

        res['response']['text'] = get_text_question(user_id)
        give_question_buttons(res, user_id)

        USERS[user_id]['tips'] = {
            'Доп. жизнь': 'В текущем вопросе вам даётся право на ошибку',
            '50 на 50': 'Остаётся два варианта ответа, один из который правильный',
            'Звонок другу': 'Помощь друга',
            'Помощь зала': 'Зрители голосуют за понравившиеся им варианты ответов'
        }
        return







    flag = False
    for w in TOP_WORDS:
        if w in user_proposition:
            flag = True
            break

    if flag:
        text_= ''
        for i in range(min(len(TOPLIST), 10)):
            text_ += str(i + 1) + ') ' + TOPLIST[i][1] + ' - ' + str(TOPLIST[i][0]) + '\n'
        res['response']['text'] = 'Топ игроков игры "Интеллектуальный Олимп"\n\n' + text_

        give_change_or_toplist_buttons(res, user_id)

        return


    text_ = 'Простите, но я не совсем поняла вас, повторите ещё раз.'
    res['response']['text'] = text_

    give_change_or_toplist_buttons(res, user_id)

    return

def give_hint(res, req, user_id):
    user_words = req['request']['nlu']['tokens']
    user_proposition = req['request']['original_utterance'].lower().replace('  ', ' ')

    if len(USERS[user_id]['tips']) == 0:
        res['response']['text'] = 'Увы, но у вас кончились подсказки.'
        give_question_buttons(res, user_id)
        return

    res['response']['text'] = 'Вам доступны следующие подсказки:\n'
    res['response']['buttons'] = []

    for t in USERS[user_id]['tips']:
        res['response']['text'] += t + ' - ' + USERS[user_id]['tips'][t] + '\n'
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
    USERS[user_id]['game_status'] = 6
    return


def check_for_user_give_tip(res, req, user_id):
    user_words = req['request']['nlu']['tokens']
    user_proposition = req['request']['original_utterance'].lower().replace('  ', ' ')

    # Без подсказок
    flag = False
    for w in REFUSAL_TIP:
        if w in user_proposition:
            flag = True
            break

    if flag:
        USERS[user_id]['game_status'] = 2
        res['response']['text'] = random.choice(WITHOUT_PROMPT)
        give_question_buttons(res, user_id)
        return


    flag = False
    for w in EXTRA_LIFE:
        if w in user_proposition:
            flag = True
            break

    if flag:
        if 'Доп. жизнь' not in USERS[user_id]['tips']:
            give_question_buttons(res, user_id)
            res['response']['text'] = 'Увы, но вы уже использовали этот бонус! Выберите ответ.'
            return

        USERS[user_id]['count_wrong'] = 1
        USERS[user_id]['game_status'] = 2
        USERS[user_id]['tips'].pop('Доп. жизнь')
        give_question_buttons(res, user_id)
        res['response']['text'] = 'Бонус активирован! У вас есть право ошибиться на текущем вопросе!'
        return


    flag = False
    for w in FIFTY_FIFTY:
        if w in user_proposition:
            flag = True
            break

    if flag:
        if '50 на 50' not in USERS[user_id]['tips']:
            res['response']['text'] = 'Увы, но вы уже использовали этот бонус! Выберите ответ.'
            give_question_buttons(res, user_id)
            USERS[user_id]['game_status'] = 2
            return

        arr = []
        for maybe in USERS[user_id]['question']['possible']:
            if maybe.upper() != USERS[user_id]['question']['correct_answer'].upper():
                arr.append(maybe)

        random.shuffle(arr)
        while len(arr) > 1:
            USERS[user_id]['question']['possible'].pop(arr[0])
            del arr[0]

        USERS[user_id]['tips'].pop('50 на 50')
        give_question_buttons(res, user_id)
        USERS[user_id]['game_status'] = 2
        res['response']['text'] = 'Мы убрали лишние ответы! Делайте выбор!'
        return


    flag = False
    for w in CALL_TO_FRIEND:
        if w in user_proposition:
            flag = True
            break


    if flag:
        if 'Звонок другу' not in USERS[user_id]['tips']:
            res['response']['text'] = 'Вы уже использовали этот бонус! Выберите ответ.'
            USERS[user_id]['game_status'] = 2
            give_question_buttons(res, user_id)
            return

        USERS[user_id]['tips'].pop('Звонок другу')
        arr = []
        for g in USERS[user_id]['question']['possible']:
            arr.append(g)

        USERS[user_id]['game_status'] = 2
        give_question_buttons(res, user_id)
        res['response']['text'] = USERS[user_id]['question']['call_friend'].format(random.choice(arr))
        res['response']['text'] += '\n' + random.choice(TIME_ENDED)
        return


    flag = False
    for w in HELP_HALL:
        if w in user_proposition:
            flag = True
            break


    if flag:
        if 'Помощь зала' not in USERS[user_id]['tips']:
            res['response']['text'] = 'Вы уже использовали эту подсказку! Пора выбрать ответ.'
            USERS[user_id]['game_status'] = 2
            give_question_buttons(res, user_id)
            return

        USERS[user_id]['tips'].pop('Помощь зала')
        text_ = 'Зрители берут в руки пульты и голосую!..\n Голосование закончилось!\n Результаты следующие:\n'
        cnt = 0
        for w in USERS[user_id]['question']['possible']:
            cnt += USERS[user_id]['question']['statistics'][w]

        STAT = ''
        for w in string_variant.upper():
            if w in USERS[user_id]['question']['possible']:
                STAT += w + ' - ' + str(int(100 * USERS[user_id]['question']['statistics'][w] / cnt)) + '%\n'

        text_ += STAT

        res['response']['text'] = text_ + '\nАнализируйте и делайте ваш выбор!'
        give_question_buttons(res, user_id)
        USERS[user_id]['game_status'] = 2
        return

    text_ = 'Я не совсем поняла какую подсказку вы выбрали, повторите ещё раз!'
    res['response']['text'] = text_
    res['response']['buttons'] = []
    for t in USERS[user_id]['tips']:
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
    USERS[user_id]['game_status'] = 6
    return


def update_statistics(question_id, symbol, delta):
    QUESTIONS.update_question_statistics(question_id, symbol, delta)


def give_result_and_ask_nickname(res, user_id):
    res['response']['text'] = '{}, вы набрали {} очков! Под каким именем вас записать в топ-лист?'.format(
        USERS[user_id]['name'], USERS[user_id]['points'])
    USERS[user_id]['game_status'] = 3
    return




@app.route('/toplist', methods=['GET'])
def index():
    NEW_ARR = []
    for i in range(len(TOPLIST)):
        NEW_ARR.append([i, TOPLIST[i][1], TOPLIST[i][0]])

    return render_template('delete_top.html', TOP_USERS = NEW_ARR)


@app.route('/delete_top/<id>', methods=['GET'])
def delete_top(id):
    del TOPLIST[int(id)]
    save_toplist()
    return redirect('/toplist')


@app.route('/questions', methods=['GET'])
def questions_page():
    DATA = []
    for i in categories:
        ALL = QUESTIONS.get_all_by_category(i)
        DATA.append((categories[i], i, ALL))

    return render_template('delete_some_questions.html', questions_ = DATA)




@app.route('/delete_question/<id>', methods=['GET'])
def del_quest(id):
    try:
        id_del = int(id)
        QUESTIONS.delete_question_by_id(id)
    except:
        return redirect('/questions')
    return redirect('/questions')



from flask_wtf import FlaskForm
class ADD_NEW_QUESTION(FlaskForm):

    cat = []
    for i in categories:
        cat.append((str(i), categories[i]))

    category = SelectField('Category:', choices = cat)

    text = StringField('Text:', validators=[])
    tip = StringField('Звонок другу:', validators=[])

    poin = []
    poin.append(('50', '50'))
    for i in range(1, 16):
        poin.append((str(100 * i), str(100 * i)))

    points = SelectField('Points:',choices = poin)



    a_var = StringField('А:', validators=[])
    b_var = StringField('Б:', validators=[])
    c_var = StringField('В:', validators=[])
    d_var = StringField('Г:', validators=[])


    correct_answer = SelectField('Correct_answer:', choices=[('А','А'),('Б','Б'), ('В','В'),('Г','Г') ])

    level = SelectField('LEVEL:', choices=[('1','1'),('2','2'), ('3','3'),('4','4'), ('5','5') ])



    submit = SubmitField('Отправить')


@app.route('/add_new_question', methods=['GET', 'POST'])
@app.route('/add_question', methods=['GET', 'POST'])
def add_new_question():
    form = ADD_NEW_QUESTION()
    if form.validate_on_submit():
        try:
            category = form.category.data
            text = form.text.data.strip()
            tip = form.tip.data.strip()
            points = int(form.points.data)

            a_var = form.a_var.data.strip()
            b_var = form.b_var.data.strip()
            c_var = form.c_var.data.strip()
            d_var = form.d_var.data.strip()
            correct_answer = form.correct_answer.data.strip()
            level = int(form.level.data)


            QUESTIONS.insert_by_category(category, text, a_var, b_var, c_var, d_var, tip, correct_answer,level, points)
            return redirect('/questions')
        except:
            return render_template('add_new_quest.html', form=form, categories=categories, code_id=3)

    return render_template('add_new_quest.html', form=form, categories=categories, code_id=1)


class UPDATE_QUESTION_FORM(FlaskForm):
   # def __init__(self, name_category, text_question, call_friend, now_points, a, b, c,d, correct_ans, level_quest):
        cat = []
        for i in categories:
            cat.append((str(i), categories[i]))

        category = SelectField('Category:',  choices = cat)
        text = StringField('Text:',  validators=[])
        tip = StringField('Звонок другу:', validators=[])

        poin = []
        poin.append(('50', '50'))
        for i in range(1, 16):
            poin.append((str(100 * i), str(100 * i)))

        points = SelectField('Points:', choices = poin)



        a_var = StringField('А:', validators=[])
        b_var = StringField('Б:', validators=[])
        c_var = StringField('В:', validators=[])
        d_var = StringField('Г:', validators=[])


        correct_answer = SelectField('Correct_answer:', choices=[('А','А'),('Б','Б'), ('В','В'),('Г','Г') ])

        level = SelectField('LEVEL:',  choices=[('1','1'),('2','2'), ('3','3'),('4','4'), ('5','5') ])
        submit = SubmitField('Отправить')




@app.route('/update_question/<id>', methods=['GET', 'POST'])
def update_question_f(id):
    id_ = id

    quest = QUESTIONS.get(id_)
    print(quest[1])
    form = UPDATE_QUESTION_FORM(
    category = quest[1],
    text = quest[2],
    tip = quest[11],
    points = quest[14],
    a_var = quest[3],
    b_var = quest[4],
    c_var = quest[5],
    d_var = quest[6],
    correct_answer = quest[12],
    level = quest[13]
    )

    if form.validate_on_submit():
        category = form.category.data
        if category == categories[quest[1]]:
            category = quest[1]
        text = form.text.data
        call_friend = form.tip.data
        points = form.points.data
        a = form.a_var.data
        b = form.b_var.data
        c = form.c_var.data
        d = form.d_var.data
        correct_ans = form.correct_answer.data
        level = form.level.data
        QUESTIONS.update_question(category, id, text, call_friend, points, a, b, c, d, correct_ans,level)
        return redirect('/questions')
    return render_template('update_question.html', form=form, question_=quest, categories=categories)



def give_change_or_toplist_buttons(res, user_id):
    res['response']['buttons'] = []

    res['response']['buttons'].append({
        'title': 'Остаться в кат.',
        'hide': True
    })

    res['response']['buttons'].append({
        'title': 'Поменять кат.',
        'hide': True
    })

    res['response']['buttons'].append({
        'title': 'Топ-лист',
        'hide': True
    })
    return



app.config['SECRET_KEY'] = 'e70lIUUoXRKlXc5VUBmiJ9Hdi'

if __name__ =='__main__':
    app.run()