from random import seed
from telegram.ext import Updater, ExtBot, MessageHandler, Filters, CallbackQueryHandler, CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import mysql.connector
import pandas as pd
import datetime

print("Telegram cane toad reporter is runing...")

f = open('./token.txt') # Token of Cane Toad Reporting System
TOKEN = f.read()
f.close

ADMIN_ID = "348929573" # ID of Ta-chih Chen
SUBADMIN_ID = "5049561715" # ID of Yung-lun Lin

bot = ExtBot(TOKEN)

age = {"成體": "ad", "幼體": "juv",}

yn = {"上傳": "send", "取消": "cancel",}

de = {"確認刪除": "delete", "取消": "dont_delete",}

apply = {"送出申請": "submit", "取消": "dont_submit"}

org = {
    "特有生物研究保育中心": "tesri",
    "東華大學": "ndhu",
    "台灣兩棲類動物保育協會": "tacv",
    "台中市野生動物保育學會": "twcg",
    "南投林區管理處": "nfb",
    "南投縣政府": "ncg",
    "其他": "other",
}

# habitat_bt = {
#     "稻田": "RF",
#     "收割稻田": "HRF",
#     "菜園":"VF",
#     "果園": "OR",
#     "空地": "BA",
#     "住宅區": "UB",
#     "溝渠": "DI",
#     "溪流": "ST",
#     "水池": "WP",
#     "人工建物": "BU",
#     "其他": "OT"
# }

habitat_bt = ("稻田", "收割稻田", "草生地", "菜園", "果園", "裸露地", "住宅區", "溝渠", "溪流", "水池", "樹林", "道路", "其他")

applying = [] # temperating list for appliers. make sure the users who is not applier evoke the mes_reation()

user_location = pd.DataFrame({"x": [], "y":[], "age":[], "habitat": [], "user_id":[], "observer": [], "datetime":[]})
user_location["user_id"] = user_location["user_id"].astype(str)
# user_location["user_id"] = user_location["user_id"].astype(int)

user_last_row = pd.DataFrame({"user_id": [], "row_id": [], "datetime": []})
user_last_row["user_id"] = user_last_row["user_id"].astype(str)

user_org = pd.DataFrame({"user_id": [], "org": []})


def cursor_setting():
    """setting the mysql connection on localhost, to database
    """
    global canetoad_conn, canetoad_cursor

    f = open('./password.txt')
    mysql_password = f.read()
    f.close

    canetoad_conn = mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = mysql_password,
        database = "canetoaddemo"
    )

    canetoad_cursor = canetoad_conn.cursor()


def pop_user_selection(user_id, data_table):
    ouput = data_table[data_table["user_id"] != user_id]
    return ouput


def start(update, context):
    """
    This function will be called when user sending a location type message
    """

    global user_location
    mysql_error_2013 = "2013 (HY000): Lost connection to MySQL server during query"

    try:
        canetoad_cursor.execute("SELECT telegram_id FROM bfsduckdb.user WHERE verify = 1;")
        ver_id = [i[0] for i in canetoad_cursor.fetchall()]

    except Exception as e:
        if str(e) == mysql_error_2013:
            bot.send_message(ADMIN_ID, "mysql disconnection detected")
            canetoad_conn.reconnect(attempts = 3, delay = 0)
            bot.send_message(ADMIN_ID, "mysql reconnected")
            canetoad_cursor.execute("SELECT telegram_id FROM bfsduckdb.user WHERE verify = 1;")
            ver_id = [i[0] for i in canetoad_cursor.fetchall()]

    user_id = str(update.message.chat.id)

    if user_id not in ver_id:
        bot.send_message(user_id, '你還沒有使用回報系統的權限\n請輸入"/signup"跟管理員申請')
        return

    user_location = pop_user_selection(user_id, user_location)

    x = update.message.location.longitude
    y = update.message.location.latitude


    user_location = user_location.append({"x": x, "y": y, "age": None,"habitat": None, "user_id": user_id, "observer": None, "datetime":None}, ignore_index=True)


    bot.send_message(user_id, '這隻海蟾蜍是成體還是幼體?',
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(i, callback_data = age[i]) for i in age.keys()]]))


def bt_reaction(update, context):
    global user_location, user_last_row
    callback = update.callback_query.data
    user_id = str(update.callback_query.message.chat.id)
    user_sel = user_location[user_location["user_id"] == user_id].index

    if callback == "ad" or callback == "juv":

        if len(user_sel) == 0:
            bot.send_message(user_id, '請先選擇一個點位!')
            return

        elif callback == "ad":
            user_location.loc[user_location['user_id'].map(lambda x: user_id == x), 'age'] = callback
            bot.send_message(user_id, '你選擇了成體')

        elif callback == "juv":
            user_location.loc[user_location['user_id'].map(lambda x: user_id == x), 'age'] = callback
            bot.send_message(user_id, '你選擇了幼體')

        bot.send_message(user_id, '請選擇一個棲地類型', reply_markup = ReplyKeyboardMarkup([[i] for i in habitat_bt], resize_keyboard=True))


    elif callback == "send":
        age_sel = user_location[user_location["user_id"] == user_id]["age"]
        hab_sel = user_location[user_location["user_id"] == user_id]["habitat"]

        if len(user_sel) == 0:
            bot.send_message(user_id, '請先選擇一個點位!')

        elif len(user_sel) == 1:

            if len(age_sel) == 1:

                if not age_sel.values[0]:
                    bot.send_message(user_id, '請先選擇成幼!')
                    return

                elif len(hab_sel) == 1:

                    if not hab_sel.values[0]:
                        bot.send_message(user_id, '請先選擇棲地類型!')
                        return

                    dt = datetime.datetime.strptime(str(update.callback_query.message.date)[:-6], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=8)
                    first_name = update.callback_query.message.chat.first_name
                    last_name = update.callback_query.message.chat.last_name
                    observer = first_name + " " + last_name

                    user_location.loc[user_location['user_id'].map(lambda x: user_id == x), 'observer'] = observer

                    user_location.loc[user_location['user_id'].map(lambda x: user_id == x), 'datetime'] = dt

                    bot.send_message(user_id, '資料已成功上傳!\n上傳下一筆紀錄請再分享一個新的點位')

                    sql = "INSERT INTO cane_toad (x, y, age, habitat, telegram_id, observer, datetime) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    tosql = tuple(user_location[user_location["user_id"] == user_id].values.tolist()[0])
                    canetoad_cursor.execute(sql, tosql)
                    canetoad_conn.commit()
                    print("%s send one data %s" % (observer, dt))
                    user_location = pop_user_selection(user_id, user_location)

                    user_last_row = pop_user_selection(user_id, user_last_row)
                    canetoad_cursor.execute("SELECT id FROM canetoaddemo.cane_toad WHERE telegram_id = '%s' ORDER BY id DESC LIMIT 0, 1" % user_id)
                    last_id = str(canetoad_cursor.fetchone()[0])
                    user_last_row = user_last_row.append({"user_id":user_id, "row_id": last_id, "datetime":dt}, ignore_index=True)


    elif callback == "delete": # deleting commit in sql datebase
        row_id = int(user_last_row.loc[user_last_row['user_id'].map(lambda x: user_id == x), 'row_id'].values[0])
        canetoad_cursor.execute("SET SQL_SAFE_UPDATES = 0")
        canetoad_conn.commit()
        canetoad_cursor.execute("DELETE FROM cane_toad WHERE id = %i" % row_id)
        canetoad_cursor.execute("SET SQL_SAFE_UPDATES = 1")
        canetoad_conn.commit()
        bot.send_message(user_id, "資料已刪除成功！")

        first_name = update.callback_query.message.chat.first_name
        last_name = update.callback_query.message.chat.last_name
        observer = first_name + " " + last_name
        print(observer + " " + "deleted an observation which id is %s" % row_id)

    elif callback == "dont_delete":
        bot.send_message(user_id, "刪除已取消")
        return

    elif callback == "submit": # intsert sign up data to mysql database
        first_name = update.callback_query.message.chat.first_name
        last_name = update.callback_query.message.chat.last_name
        user_name = first_name + " " + last_name
        organization = user_org.loc[user_org['user_id'].map(lambda x: user_id == x), 'org'].values[0]

        sql = "INSERT INTO account (user_name, telegram_id, verify, org) VALUES (%s, %s, %s, %s)"
        tosql = (user_name, user_id, 0, org[organization])
        canetoad_cursor.execute(sql, tosql)
        canetoad_conn.commit()

        bot.send_message(user_id, '你的申請已經送出\n請等待管理員審核')
        bot.send_message(ADMIN_ID, '%s from %s submitted the application' % (user_name, organization))

    elif callback == "cancel":
        user_location = pop_user_selection(user_id, user_location)
        bot.send_message(user_id, '此筆紀錄已取消!\n上傳新紀錄請再分享一個新的點位')


def mes_reaction(update, context):
    user_mes = update.message.text
    user_id = str(update.message.chat.id)

    user_sel = user_location[user_location["user_id"] == user_id].index
    age_sel = user_location[user_location["user_id"] == user_id]["age"]

    if user_mes in habitat_bt: # habitat selection

        if len(user_sel) == 0:
            bot.send_message(user_id, '請先選擇一個點位!')

        elif len(user_sel) == 1:

            if len(age_sel) == 1:

                if not age_sel.values[0]:
                    bot.send_message(user_id, '請先選擇成幼!')
                    return

                user_location.loc[user_location['user_id'].map(lambda x: user_id == x), 'habitat'] = user_mes
                bot.send_message(user_id, '你選擇了%s' % user_mes)
                bot.send_message(user_id, '按"確認"上傳資料，按"取消"重來\n重新回報請再分享一個新的點位', reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(i, callback_data = yn[i]) for i in yn.keys()]]))
                return

    canetoad_cursor.execute("SELECT telegram_id FROM canetoaddemo.account WHERE verify = 0;")
    tg_id = [i[0] for i in canetoad_cursor.fetchall()]

    if user_mes in tg_id and user_id == ADMIN_ID: # admin update the vetify in mysql database
        canetoad_cursor.execute("UPDATE account SET verify = 1 WHERE telegram_id = %s" % user_mes)
        canetoad_conn.commit()
        bot.send_message(ADMIN_ID, '%s have been vertified' % user_mes)
        bot.send_message(user_id, '你的申請已經通過了!')

    if user_mes in list(org.keys()) and user_id in applying: # listen the oranization sent from user
        applying.remove(user_id)
        user_org.loc[user_org['user_id'].map(lambda x: user_id == x), 'org'] = org[user_mes]
        bot.send_message(user_id, "你選擇了%s" % user_mes)

        bot.send_message(user_id, '確認送出申請?',
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(i, callback_data = apply[i]) for i in apply.keys()]]))


def signup(update, context):
    global user_org
    user_id = str(update.message.chat.id)
    canetoad_cursor.execute("SELECT telegram_id FROM canetoaddemo.account;")
    tg_id = [i[0] for i in canetoad_cursor.fetchall()]

    if user_id in [ADMIN_ID, SUBADMIN_ID]:
        bot.send_message(user_id, 'You are already an admin')
        return

    elif str(user_id) in tg_id:
        bot.send_message(user_id, '你已經申請通過了\n或者是管理員還正在審核')
        return

    applying.append(user_id)
    user_org = user_org.append({"user_id": user_id, "org": None}, ignore_index=True)

    first_name = update.message.chat.first_name

    bot.send_message(user_id, 'Hi! %s!\n感謝你願意來幫忙移除海蟾蜍\n請問你服務的單位是？' % first_name, reply_markup = ReplyKeyboardMarkup([[i] for i in org.keys()], resize_keyboard=True))


def authorize(update, context):
    user_id = str(update.message.chat.id)

    if user_id != ADMIN_ID:
        bot.send_message(user_id, 'You have no right to execute this command')
        return

    canetoad_cursor.execute("SELECT user_name, telegram_id FROM canetoaddemo.account WHERE verify = 0;")
    tg_id = [[i[0],i[1]] for i in canetoad_cursor.fetchall()]

    if len(tg_id) == 0:
        bot.send_message(user_id, 'All users have been autherized')
        return

    bot.send_message(user_id, 'select the user for autherizing', reply_markup = ReplyKeyboardMarkup([i for i in tg_id], resize_keyboard=True))


def contact(update, context):
    user_id = str(update.message.chat.id)
    bot.send_message(user_id, "統籌策劃：林湧倫")
    bot.send_contact(user_id, phone_number = "+886986915873", first_name = "Yong-Lun")
    bot.send_message(user_id, "系統開發：陳達智")
    bot.send_contact(user_id, phone_number = "+886912957551", first_name = "Ta-chih")


def delete(update, context):
    canetoad_cursor.execute("SELECT telegram_id FROM canetoaddemo.account WHERE verify = 1;")
    ver_id = [i[0] for i in canetoad_cursor.fetchall()]
    user_id = str(update.message.chat.id)

    row_dt = pd.to_datetime(user_last_row.loc[user_last_row['user_id'].map(lambda x: user_id == x), 'datetime'].values)
    now_dt = datetime.datetime.now()

    row_id = user_last_row.loc[user_last_row['user_id'].map(lambda x: user_id == x), 'row_id'].values

    if user_id not in ver_id:
        bot.send_message(user_id, 'You have no right to execute this command')
        return

    elif len(row_id) == 0:
        bot.send_message(user_id, "先上傳紀錄才有紀錄可以刪除喔！")
        return

    elif now_dt - row_dt[0] > datetime.timedelta(minutes=5):
        bot.send_message(user_id, "上一筆紀錄已經超過5分鐘，需要修改請直接聯絡系統管理員\n輸入 /contact 顯示聯絡資訊")
        return

    canetoad_cursor.execute("SELECT age, habitat FROM canetoaddemo.cane_toad WHERE id = %i" % int(row_id[0]))
    last_recoed = [i for i in canetoad_cursor.fetchall()]

    bot.send_message(user_id, '你確定要刪除上一筆紀錄?\n上一筆紀錄：\n成幼為：%s 環境為：%s' % (last_recoed[0][0], last_recoed[0][1]), reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(i, callback_data = de[i]) for i in de.keys()]]))

def help(update, context):
    user_id = str(update.message.chat.id)
    bot.send_message(user_id, "\n/signup - 申請回報權限\n/delete - 刪除上一筆資料(5分鐘內)\n/contact - 聯絡回報系統負責人")

cursor_setting()
updater = Updater(TOKEN)
updater.dispatcher.add_handler(CommandHandler('signup', signup))
updater.dispatcher.add_handler(CommandHandler('authorize', authorize))
updater.dispatcher.add_handler(CommandHandler('contact', contact))
updater.dispatcher.add_handler(CommandHandler('delete', delete))
updater.dispatcher.add_handler(CommandHandler("help", help))
updater.dispatcher.add_handler(MessageHandler(Filters.location, start))
updater.dispatcher.add_handler(MessageHandler(Filters.text, mes_reaction))
updater.dispatcher.add_handler(CallbackQueryHandler(bt_reaction))
updater.start_polling()
updater.idle()