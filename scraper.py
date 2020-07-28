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