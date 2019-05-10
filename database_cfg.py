import sqlite3


class DB:
    def __init__(self):
        conn = sqlite3.connect('db.db', check_same_thread=False)
        self.connection = conn

    def get_connection(self):
        return self.connection

    def __del__(self):
        self.connection.close()


categories = {
    '1': 'Химия',
    '2': 'Биология',
    '3': 'Искусство',
    '4': 'Физика',
    '5': 'Литература',
    '6': 'История',
    '7': 'Супер-викторина'
}

RUSCHAR_TO_ENCHAR = {
    'а': 'a',
    'б': 'b',
    'в': 'c',
    'г': 'd'
}

category_name = 'category_'
class QuestionsModel:
    def __init__(self, data_base):
        self.connection = data_base.get_connection()
        self.init_table()

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS questions
                                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                 category TEXT,
                                 text_question TEXT,
                                 a ТЕХТ,
                                 b TEXT,
                                 c TEXT,
                                 d TEXT,
                                 statistic_a INTEGER,
                                 statistic_b INTEGER,
                                 statistic_c INTEGER,
                                 statistic_d INTEGER,
                                 tip text,
                                 correct_answer VARCHAR(1),
                                 level INTEGER,
                                 points INTEGER
                                 )''')
        cursor.close()
        self.connection.commit()

    def insert_by_category(self, category, text, a, b, c, d, tip, correct_answer, level, points):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO questions
                          ( 
                                 category,
                                 text_question,
                                 a,
                                 b,
                                 c,
                                 d,
                                 statistic_a,
                                 statistic_b,
                                 statistic_c,
                                 statistic_d,
                                 tip,
                                 correct_answer,
                                 level,
                                 points ) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (category, text, a, b, c, d, 1, 1, 1, 1, tip, correct_answer, level, points))
        cursor.close()
        self.connection.commit()

    def get(self, id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM questions WHERE id = ?", (str(id),))
        row = cursor.fetchone()
        return row

    def get_all_by_category(self, category):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM questions WHERE category = ?", (str(category), ))
        rows = cursor.fetchall()
        return rows

    def delete_question_by_id(self, id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM questions WHERE id = ?''', (str(id),))
        cursor.close()
        self.connection.commit()

    def __str__(self):
        data = []
        for id_category in categories:
            data.append(self.get_all_by_category(id_category))
        return str(data)

    def update_question_statistics(self, question_id, symbol, delta):
        cursor = self.connection.cursor()
        char_ = RUSCHAR_TO_ENCHAR[symbol.lower()]
        column = 'statistic_' + char_
        cursor.execute('''UPDATE questions SET {} = {} + {} WHERE id = ?'''.format(str(column), str(column), str(delta)), (str(question_id),)  )
        cursor.close()
        self.connection.commit()

    def update_question(self, category_, id, text, call_friend, points, a, b, c, d, correct_ans,level):
        cursor = self.connection.cursor()
        cursor.execute('''UPDATE questions SET category = '{}', text_question ='{}', a ='{}', b ='{}', c ='{}', d ='{}',  tip = '{}',  correct_answer='{}', points='{}', level='{}' WHERE id = ?'''.format(
                                                                                    str(category_),
                                                                                    text,
                                                                                    a,
                                                                                    b,
                                                                                    c,
                                                                                    d,
                                                                                    call_friend,
                                                                                    correct_ans,
                                                                                    points,
                                                                                    level
                                                                                   ), (str(id),))

        cursor.close()
        self.connection.commit()

    def get_all_by_category2(self, category):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM  {}".format('category_' + str(category)))
        rows = cursor.fetchall()
        return rows


my_db = DB()
QUESTIONS = QuestionsModel(my_db)

#QUESTIONS.insert_by_category(2, 'Как жить на земле?!', 'макака', 'еврей', 'Обезьяна', 'Кардон', 'Отвечает Сергей Морозов: "Я полагая ответ - А"', 'А', 2, 300)


#QUESTIONS.delete_question_by_category_and_id(1, 4)

