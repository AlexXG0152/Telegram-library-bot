#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pyzbar.pyzbar as pyzbar
from search_engine_parser import GoogleSearch
import cv2
import sqlite3
import telebot
from telebot import types
import asyncio


TOKEN = "TOKEN:TELEGRAM_BOTFATHER_TOKEN"
bot = telebot.AsyncTeleBot(TOKEN)



@bot.message_handler(commands=["start"])
def send_welcome(message):
    start_keyboard = types.InlineKeyboardMarkup()
    start_registration = types.InlineKeyboardButton(text='Регистрация', callback_data='registration')
    start_login = types.InlineKeyboardButton(text='Вход', callback_data='login')
    start_keyboard.add(start_registration)
    start_keyboard.add(start_login)
    bot.send_message(message.chat.id, 'Привет!', reply_markup=start_keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_btn(call):
    if call.data == "registration":
        send_login(call.message)
    elif call.data == "login":
        send_login(call.message)


user_data = {}


class User_register:
    def __init__(self, login):
        self.login = login
        self.password = " "


def send_login(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    msg = bot.send_message(message.chat.id, "Введите логин: ", reply_markup=markup).wait()# add wait() bcos async
    bot.register_next_step_handler(msg, send_password)


def send_password(message):
    user_id = message.from_user.id
    user_data[user_id] = User_register(message.text)
    msg = bot.send_message(message.chat.id, "Введите пароль: ").wait()#
    bot.register_next_step_handler(msg, last_process)


def login(nameuser, user_password):
    log = True
    while log is True:
        user = nameuser
        password = user_password
        con = sqlite3.connect('site.sqlite')
        cur = con.cursor()
        cur.execute("""SELECT * FROM USER
                       WHERE NAME=? AND PASSWORD=?""", (user, password))
        if cur.fetchone() is not None:
            print(f"Welcome, {user}")
            userdata = cur.execute("""SELECT * FROM USER
                                      WHERE NAME=?
                                      AND PASSWORD=?""", (user, password))
            userdatareturn = userdata.fetchone()
            userid = userdatareturn[0]
            return user, userid, False, True
        else:
            print("Login failed")
            log = False
            return _, _, _, False


def last_process(message):
        user_id = message.from_user.id
        user = user_data[user_id]
        nameuser = user.login
        user_password = message.text
        print(nameuser, user_password) 
        _, _, _, result = login2(nameuser, user_password)
        print(result)
        if result is True:
            bot.send_message(message.chat.id, "Вы успешно вошли.").wait()
            login_is_true()
        else:
            bot.send_message(message.chat.id, "Ты Кто?").wait()
            pass


def login_is_true():
    login_is_true.is_true = True
    pass

login_is_true.is_true = False


@bot.message_handler(commands=["keys"])
def send_commands(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('users', 'books')
    markup.row('c', 'd', 'e')
    bot.send_message(message.chat.id, "Choose one:", reply_markup=markup).wait()
    bot.register_next_step_handler(message, buttons_callback)


@bot.callback_query_handler(func=lambda call: True)
def buttons_callback(message):
    print(message.text)
    if message.text == "users":
        users = read_user(userid)
        [(bot.send_message(message.chat.id, str(i))) for i in users]
    elif message.text == "books":#
        books = read(userid)
        [(bot.send_message(message.chat.id, str(i))) for i in books]


@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    print(f"LOGIN STATUS: {login_is_true.is_true}")
    if login_is_true.is_true == True:
        try:
            chat_id = message.chat.id
            file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id).wait()
            downloaded_file = bot.download_file(file_info.file_path).wait()
            src = 'D:/temp/' + file_info.file_path
            with open(src, 'wb') as new_file:
                new_file.write(downloaded_file)

            bot.reply_to(message, "Пожалуй, я сохраню это")
            asyncio.run(create(userid, src))
            read(userid)

        except Exception as e:
            print(e)
            bot.reply_to(message, e)
    else:
        send_welcome(message)


async def getImage(src):
    im = cv2.imread(src)
    decodedObjects = await decode(im)
    isbn = decodedObjects[0][0].decode()
    return isbn


async def decode(im):
    # Find barcodes and QR codes
    decodedObjects = pyzbar.decode(im)
    # Print results
    for obj in decodedObjects:
        print('Type : ', obj.type)
        print('Data : ', obj.data, '\n')
    return decodedObjects


async def google(src):
    query = await getImage(src)
    search_args = (query, 1)
    gsearch = GoogleSearch()
    gresults = await gsearch.async_search(*search_args)
    return query, gresults['titles'][0]


def connect():
    con = sqlite3.connect('site.sqlite')
    print("Database opened successfully")
    return con


def table_books():
    con =  connect()
    cur = con.cursor()
    cur.execute('''CREATE TABLE BOOKS
        (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        ISBN TEXT NOT NULL,
        USER_ID INT NOT NULL,
        NAMEBOOK TEXT NOT NULL,
        TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL);''')
    print("Table created successfully")
    con.commit()
    con.close()


async def create(userid, src):
    isbn, namebook = await google(src)
    con =  connect()
    cur = con.cursor()
    cur.execute('''INSERT INTO
        BOOKS(ISBN, USER_ID, NAMEBOOK)
        VALUES (?, ?, ?)''', (isbn, userid, namebook))
    con.commit()
    print("Record inserted successfully")
    con.close()


def read(userid):
    userid = int(userid)
    con =  connect()
    cur = con.cursor()
    cur.execute("""SELECT ID, ISBN, USER_ID, NAMEBOOK, TIME
                   FROM BOOKS WHERE USER_ID=?""", [userid])
    rows = cur.fetchall()
    print("Operation done successfully")
    con.close()
    return rows


def update():  # THINKABOUTIT
    con =  connect()
    cur = con.cursor()
    idbook = str(input("idbook "))
    cur.execute("UPDATE BOOKS SET AGE = 20 WHERE ID = ?", idbook)
    con.commit()
    print("Total updated rows:", cur.rowcount)
    cur.execute("SELECT ID, ISBN, USER_ID, NAMEBOOK, TIME FROM BOOKS")
    rows = cur.fetchall()
    read_rows(rows)
    print("Operation done successfully")
    con.close()


def delete(userid):  # THINKABOUTIT
    con =  connect()
    cur = con.cursor()
    idbook = str(input("idbook "))
    cur.execute("DELETE FROM BOOKS WHERE ID=? AND USER_ID=?", [idbook, userid])
    con.commit()
    print("Total deleted rows:", cur.rowcount)
    cur.execute("SELECT ID, ISBN, USER_ID, NAMEBOOK, TIME FROM BOOKS")
    rows = cur.fetchall()
    read_rows(rows)
    print("Deletion successful")
    con.close()


def compare_book(userid):
    query = getImage()
    con =  connect()
    cur = con.cursor()
    cur.execute("""SELECT ID, ISBN, USER_ID, NAMEBOOK, TIME
                   FROM BOOKS
                   WHERE USER_ID=? AND ISBN=?""", (userid, query))
    if cur.fetchone() is not None:
        print("READED!")
    else:
        print("NO")
    print("Operation done successfully")
    con.close()
    return print(query)


def read_rows(rows):
    for row in rows:
        print("ID =", row[0])
        print("ISBN =", row[1])
        print("USER_ID =", row[2])
        print("NAMEBOOK =", row[3])
        print("TIME =", row[4], "\n")


def statistics():  # THINKABOUTIT
    con =  connect()
    cur = con.cursor()


def login():
    while True:
        user = str(input("user "))
        password = str(input("pasw "))
        con =  connect()
        cur = con.cursor()
        cur.execute("""SELECT * FROM USER
                       WHERE NAME=? AND PASSWORD=?""", (user, password))
        if cur.fetchone() is not None:
            print(f"Welcome, {user}")
            userdata = cur.execute("""SELECT * FROM USER
                                      WHERE NAME=?
                                      AND PASSWORD=?""", (user, password))
            userdatareturn = userdata.fetchone()
            userid = userdatareturn[0]
            choice(userid)
            return user, userid, False
        else:
            print("Login failed")


def table_user():
    con =  connect()
    cur = con.cursor()
    cur.execute('''CREATE TABLE USER
        (USER_ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        NAME TEXT NOT NULL,
        PASSWORD TEXT NOT NULL,
        TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        ACTIVITY BOOLEAN);''')
    print("Table USER created successfully")
    con.commit()
    con.close()


def create_user():
    user = str(input("user "))
    password = str(input("pasw "))
    con =  connect()
    cur = con.cursor()
    cur.execute('''INSERT INTO
        USER(NAME, PASSWORD, ACTIVITY)
        VALUES (?, ?, 'True')''', (user, password))
    con.commit()
    print("Record inserted successfully")
    con.close()


def read_user(userid):
    if int(userid) == 1:
        con =  connect()
        cur = con.cursor()
        cur.execute("SELECT USER_ID, NAME, PASSWORD, TIME, ACTIVITY from USER")
        rows = cur.fetchall()
        info = []
        for row in rows:
            info.append(row)
            print("ID =", row[0])
            print("name =", row[1])
            print("PASSWORD =", row[2])
            print("TIME =", row[3])
            print("ACTIVITY =", row[4], "\n")
        print("Operation done successfully")
        con.close()
        return info
    else:
        print("You are haven't rights for read this.")
        choice(userid)


def choice(userid):
    choice = int(input("""Input:
            1 - see all users,
            2 - create user,
            3 - see books \n"""))
    if choice == 1:
         read_user(userid)
    elif choice == 2:
         create_user()
    elif choice == 3:
         read(userid)


# Main
if __name__ == '__main__':
    user, userid, _ =  login()
    bot.infinity_polling(none_stop=True)


