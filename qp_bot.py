import json
import requests
import time
import datetime
import urllib
from db_helper import DBHelper
from config import TOKEN, options, operation, admins, avail_days, days_of_week, group_id

db = DBHelper()


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
    
def get_weekday_date(day_):
    days_dict = {'Monday':0, 'Tuesday':1, 'Wednesday':2, 'Thursday':3, 'Friday':4, 'Saturday':5, 'Sunday':6}
    today_wd = datetime.date.today().weekday()
    return (datetime.date.today() + datetime.timedelta(days = days_dict[day_] - today_wd)).strftime('%d/%m/%Y')
    
def handle_updates(updates):
    global operation
    global avail_days
    #Read message
    for update in updates['result']:
        if update["message"]["chat"]["type"] == 'group': continue
        text = update["message"]["text"]
        chat = update["message"]["chat"]["id"]
        username = update["message"]["chat"]["username"]
    #Info update
        if text == 'Info':
            games = db.get_games()        
            keyboard = build_keyboard(options)
            send_message('Games this week:\n', chat, keyboard)
            for day in games:
                count_players = db.count_players(day)[0][0]  
                players = db.get_players(day)   
                message = ('\n'.join(players))
                send_message('*' + day + '*' + ' ' + get_weekday_date(day) + ' *('+str(count_players) + '/9*) \n' + message, chat)
    #Checking in/out
        elif text == 'Check-in/Out':
            operation = 'check'
            games = db.get_games()
            keyboard = build_keyboard(['Check-in', 'Check-out', 'Back'])
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
                free_places = 9 - db.count_players(text)[0][0]
                message = "Checked-in for " + text
                keyboard = build_keyboard(options)
                send_message(message, chat, keyboard)
                send_message('@' + username.replace("_", "\_") + ' checked-in on ' + text + ' ' + get_weekday_date(text) + '\n' + str(free_places) + ' places remaining', group_id)
            elif db.count_players(text)[0][0] == 9:
                message = "Team is full"
                keyboard = build_keyboard(options)
                send_message(message, chat, keyboard)
            else: 
                message = "Already checked-in"
                keyboard = build_keyboard(options)
                send_message(message, chat, keyboard)
        #Check-out
        elif (text == 'Check-out') & (operation == 'check'):
            operation = 'checkout'
            games = db.get_games()
            keyboard = build_keyboard(games + ['Back'])
            send_message("Choose day", chat, keyboard)
        elif (text in days_of_week ) & (operation == 'checkout'):
            games = db.delete_player(text, username)
            message = "Checked-out for " + text
            keyboard = build_keyboard(options)
            free_places = 9 - db.count_players(text)[0][0]
            send_message(message, chat, keyboard)            
            send_message('@' + username.replace("_", "\_") + ' *checked-out* on ' + text + ' ' + get_weekday_date(text) + '\n' + str(free_places) + ' places remaining', group_id)
    #Editing games
        elif text == 'Edit games':
            if username in admins:
                operation = 'editing'
                keyboard = build_keyboard(['Add', 'Delete', 'Back'])
                send_message("Choose operation", chat, keyboard)
            else: 
                keyboard = build_keyboard(options)
                send_message("Not enough rights to edit games", chat, keyboard)                
        #Adding game
        elif (text == 'Add') & (operation == 'editing') & (username in admins):
            operation = 'adding'
            games = db.get_games()
            avail_days = [x for x in days_of_week if x not in games]
            keyboard = build_keyboard(avail_days + ['Back'])
            send_message('Choose day to add', chat, keyboard)
        elif (text in avail_days) & (operation == 'adding') & (username in admins):
            db.add_game(text, get_weekday_date(text))
            keyboard = build_keyboard(options)
            send_message('Game added on ' + text + '\n Register now at @QuizPleaseBot', chat, keyboard)    
            send_message('@' + username.replace("_", "\_") + ' added game on ' + text + ' ' + get_weekday_date(text), group_id)
        #Deleting game
        elif (text == 'Delete') & (operation == 'editing') & (username in admins):
            operation = 'deleting'
            games = db.get_games()
            avail_days = games
            keyboard = build_keyboard(avail_days + ['Back'])
            send_message('Choose day to delete', chat, keyboard)            
        elif (text in days_of_week) & (operation == 'deleting') & (username in admins):
            db.delete_game(text)
            keyboard = build_keyboard(options)
            send_message('Game deleted on' + text, chat, keyboard)
            send_message('@' + username.replace("_", "\_") + ' deleted game on ' + text + ' ' + get_weekday_date(text), group_id)
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
        #Check updates
        updates = get_updates(last_update_id)
        dates = db.get_games_dates()
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)            
        #Drop tables on Monday
        if (datetime.date.today().weekday() == 0) & (datetime.datetime.now().hour*60 + datetime.datetime.now().minute < 1):
            db.drop_games()
            db.drop_players()
            db.setup_games()
            db.setup_games()     
        #Announce games    
        for game in dates:
            if (game == (datetime.date.today()+datetime.timedelta(days=1)).strftime('%d/%m/%Y')) & (datetime.datetime.now().hour > 12):
                game_date = (datetime.date.today()+datetime.timedelta(days=1)).strftime('%d/%m/%Y')
                print(game_date)
                is_announced = db.get_is_announced_of_game(game_date)[0]
                print(is_announced)
                if is_announced == 0:
                    count_players = db.count_players(db.get_weekday_of_game(game_date)[0])[0][0]
                    print(db.get_weekday_of_game(game_date)[0])
                    print(count_players)
                    send_message('*Next game tomorrow (' + str(count_players) + '/9)*' +'\n' + 'Register now at @QuizPleaseBot', group_id)
                    db.check_as_announced(game_date)                        
        time.sleep(0.5)                     

if __name__ == '__main__':
    main()
