import json
import requests
import time
import urllib
from db_helper import DBHelper

db = DBHelper()

TOKEN = '439648466:AAGl0ljN7JWFtmE-KqimfiEwyIbh7FvnbaU'
URL = "https://api.telegram.org/bot{}/".format(TOKEN)


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    chat_username = updates["result"][last_update]["message"]["chat"]["username"]
    return (text, chat_id, username)
        
def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)

def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)
    
def handle_updates(updates):
    global operation
    global avail_days
    #Read message
    for update in updates['result']:
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        username = update["message"]["chat"]["username"]
    #Info update
        if text == 'Info':
            games = db.get_games()            
            send_message('Games this week:\n', chat)
            for day in games:
                count_players = db.count_players(day)[0][0]
                players = db.get_players(day)   
                send_message(day + ' ('+str(count_players) + '/9)\n', chat)
                message = (" ".join(players))
                send_message(message+'\n', chat)
            keyboard = build_keyboard(options)
            send_message('Choose option', chat, keyboard)
    #Checking in/out
        elif text == 'Check-in/Out':
            operation = 'check'
            games = db.get_games()
            keyboard = build_keyboard(['Check-in', 'Check-out'])
            send_message("Choose operation", chat, keyboard)
        #Check-in
        elif (text == 'Check-in') & (operation == 'check'):
            operation = 'checkin'
            games = db.get_games()
            keyboard = build_keyboard(games)
            send_message("Choose day", chat, keyboard)
        elif (text in days_of_week ) & (operation == 'checkin'):
            if db.get_one_player(text, username) == []:
                games = db.add_player(text, username)
                message = "Checked-in for " + text
                send_message(message, chat)
            else: 
                message = "Already checked-in"
                send_message(message, chat)
            keyboard = build_keyboard(options)
            send_message('Choose option', chat, keyboard)
        #Check-out
        elif (text == 'Check-out') & (operation == 'check'):
            operation = 'checkout'
            games = db.get_games()
            keyboard = build_keyboard(games)
            send_message("Choose day", chat, keyboard)
        elif (text in days_of_week ) & (operation == 'checkout'):
            games = db.delete_player(text, username)
            message = "Checked-out for " + text
            send_message(message, chat)
            keyboard = build_keyboard(options)
            send_message('Choose option', chat, keyboard)
    #Editing games
        elif text == 'Edit games':
            if username in admins:
                operation = 'editing'
                keyboard = build_keyboard(['Add', 'Delete'])
                send_message("Choose operation", chat, keyboard)
            else: 
                send_message("Not enough rights to edit games", chat)
                keyboard = build_keyboard(options)
        #Adding game
        elif (text == 'Add') & (operation == 'editing') & (username in admins):
            operation = 'adding'
            games = db.get_games()
            avail_days = [x for x in days_of_week if x not in games]
            keyboard = build_keyboard(avail_days)
            send_message('Choose day to add', chat, keyboard)
        elif (text in avail_days) & (operation == 'adding') & (username in admins):
            db.add_game(text)
            send_message('Game added on ' + text, chat)
            keyboard = build_keyboard(options)
            send_message('Choose option', chat, keyboard)
        #Deleting game
        elif (text == 'Delete') & (operation == 'editing') & (username in admins):
            operation = 'deleting'
            games = db.get_games()
            avail_days = games
            keyboard = build_keyboard(avail_days)
            send_message('Choose day to delete', chat, keyboard)
        elif (text in days_of_week) & (operation == 'deleting') & (username in admins):
            db.delete_game(text)
            send_message('Game deleted on' + text, chat)
            keyboard = build_keyboard(options)
            send_message('Choose option', chat, keyboard)
    #Other texts    
        else: 
            keyboard = build_keyboard(options)
            send_message('Choose option', chat, keyboard)
            operation = ''

def main():    
    db.setup_games()
    db.setup_players()
    last_update_id = None            
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)            
         
days_of_week = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday', 'Sunday']
operation = ''
options = ['Info', 'Check-in/Out', 'Edit games']
admins = ['pasmikh', 'olympiyae']
avail_days = []

if __name__ == '__main__':
    main()
