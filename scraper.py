#TODO использование в контексте (при переводах)
#TODO видос (команда)
#TODO видео дня

import vk_api
import json
import telebot

from tinydb import TinyDB, Query

class CredReader():
    def __init__(self, file_name):
        f = open(file_name,)
        data = json.load(f)

        self.login = data['login']
        self.password = data['password']
        self.tlgrm_token = data['tlgrm_token']

        f.close()

class Scraper():
    def __init__(self, cred_reader):
        user = cred_reader.login
        password = cred_reader.password

        self.vk_session = vk_api.VkApi(user, password)

    def auth(self):
        try:
            self.vk_session.auth(token_only=True)
        except vk_api.AuthError as error_msg:
            print(error_msg)
            return

        self.vk = self.vk_session.get_api()

    def get_my_groups(self):
        response = self.vk.groups.get()

        print(response['items'])

        # print(response)

    def get_group_info(self, group_id):
        response = self.vk.groups.get_by_id(group_id=group_id)

        response_wall = response.wall

        print(response)
        print(response_wall)

    def get_my_last_wall_message(self):
        response = self.vk.wall.get(count=1)

        if response['items']:
            print(response['items'][0])

    def get_group_last_wall_message(self, group_id):
        response = self.vk.wall.get(owner_id='-'+str(group_id), count=2)
        # первое сообщение - прикреплённое
        post = response['items'][1]
        print(post.keys())
        return post

    def search_group_by_name(self, group_name):
        response = self.vk.groups.search(q=group_name)
        group = response['items'][0]
        return group

    def prepare_post_for_bot(self, post):
        text = post['text']
        url = post['attachments'][0]['link']['url']
        desc = post['attachments'][0]['link']['description']

        print(text)
        print(desc)
        print(url)

        return f"{text}\n{desc}\n{url}"

from googletrans import Translator
from langdetect import detect

import re 

class GoogleTranslate():
    def __init__(self, split):
        self.sentense = ' '.join(x for x in split[1:])
        self.translator = Translator()
        self.russian_letters = ""

    def has_cyrillics(self, text):
        return bool(re.search('[а-яА-Я]', text))

    def run(self):
        print(self.sentense)
        # нужно обращение к API переводчика

        if self.has_cyrillics(self.sentense):
            src = "ru"
            dest = "en"
        else:
            src = "en"
            dest = "ru"

        print(f"src={src}")
        print(f"dest={dest}")

        result = self.translator\
            .translate(self.sentense, src=src, dest=dest)\
            .text
        
        return result

class NoCommand():
    def __init__(self, command):
        self.command = command

    def run(self):
        return f"{self.command} неизвестная мне команда"


# TODO подумать над названием... 
class JustSyntax():
    def __init__(self):
        pass

    def commandsHandleClassesFactory(self, command, split):
        cmd = command.lower()

        if (cmd == "перевести"  \
            or cmd == "перевод" \
            or cmd == "t" \
            or cmd == "п" \
            or cmd == "переведи"):
            
            return GoogleTranslate(split)
        else:
            return NoCommand(command)

    def analyze(self, text):
        split = text.split(" ", -1)
        output = self.commandsHandleClassesFactory(split[0], 
            split).run()
        return output
        

class TelegramBot():
    def __init__(self, cred, db):
        self.db = db
        self.bot = telebot.TeleBot(cred.tlgrm_token)

        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start_help(message):
            print(message)
            print(message.text)
            print(message.chat.id)
            success = self.db.add_user(message.chat.id)
            if (success):
                self.bot.reply_to(message, f"Я тебя запомнил {message.chat.first_name}")
            else:
                self.bot.reply_to(message, f"Ты уже у меня в базе {message.chat.first_name}")

        @self.bot.message_handler(commands=['btc'])
        def handle_btc(message):
            url = "https://blockchain.info/q/24hrprice"

        @self.bot.message_handler(func=lambda m: True)
        def handle_simple_talk(message):
            print(message.text)
            commandOutput = JustSyntax().analyze(message.text)
            self.bot.reply_to(message, commandOutput)


            

    def polling(self):
        self.bot.polling()


class TinyDbManager():
    def __init__(self, db_file_name):
        self.db = TinyDB(db_file_name)
        self.users_table = self.db.table('users')

    def add_user(self, user_id):
        User = Query()

        if (self.users_table.search(User.user_id == user_id)):
            print(f"User {user_id} already exists... ")
            return False
        else:
            self.users_table.insert({'user_id': user_id})
            print(f"successfully added user {user_id}")
            return True


cred = CredReader("cred.json")
scraper = Scraper(cred)

scraper.auth()

# популярная механика - 23553134
group = 23553134

db = TinyDbManager("db.json")
telegramBot = TelegramBot(cred, db)
telegramBot.polling()

last_post = scraper.get_group_last_wall_message(group)
telegram_post = scraper.prepare_post_for_bot(last_post)