from telegram.ext import Updater, ExtBot, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
# import mysql.connector
import pandas as pd
import datetime

print("Telegram birds reporter is runing...")
species_bt = ("黑面琵鷺", "白琵鷺",  "小水鴨", "琵嘴鴨", "赤頸鴨", "尖尾鴨", "赤膀鴨", "羅文鴨", "巴鴨")

yn = {
    "確認": "send",
    "取消": "cancel",
}

bot = ExtBot('1939444551:AAHoj_SazIr6Hpif3ZGi4uv5RWPnX3HOPBo')


sp_user = pd.DataFrame({"sp": [], "user_id": []})
sp_user["user_id"] = sp_user["user_id"].astype(int)
user_location = pd.DataFrame({"x": [], "y":[], "user_id":[]})
user_location["user_id"] = user_location["user_id"].astype(int)


# def cursor_setting():
#     """setting the mysql connection on localhost, to database
#     """

    # f = open('./password.txt')
    # mysql_password = f.read()
    # f.close

#     global paperConn, paperCursor
#     paperConn = mysql.connector.connect(
#         host = "localhost",
#         user = "root",
#         password = mysql_password,
#         database = "reportdemo"
#     )

#     paperCursor = paperConn.cursor()


def start(update, context):
    global sp_user, user_location
    x = update.message.location.latitude
    y = update.message.location.longitude
    user_id = int(update.message.chat.id)

    sp_user = sp_user[sp_user["user_id"] != user_id]
    user_location = user_location[user_location["user_id"] != user_id]

    user_location = user_location.append({"x": x, "y": y, "user_id": user_id}, ignore_index=True)
    bot.send_message(user_id, '如果要重新選擇點位，直接再分享一個點位即可', reply_markup = ReplyKeyboardMarkup([[i] for i in species_bt], resize_keyboard=True))

    bot.send_message(user_id, '請選擇你觀察到的物種，可以多選\n選完再來按這邊的"確認"\n若按錯物種，再按一次一樣的物種刪除\n按"取消"重新選擇。',
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(i, callback_data = yn[i]) for i in yn.keys()]]))


def report(update, context):
    global sp_user

    species = update.message.text
    user_id = update.message.chat.id
    user_selections = list(sp_user[sp_user["user_id"] == user_id]["sp"])

    if species in species_bt:

        if species not in user_selections:
            sp_user = sp_user.append({"sp": species, "user_id": user_id}, ignore_index=True)

            bot.send_message(user_id, "你已經選擇了: %s" % "、".join(list(sp_user[sp_user["user_id"] == user_id]["sp"])))

        elif species in user_selections:
            # bot.send_message(user_id, "%s已經選擇過了" % species)
            sp_user = sp_user[~((sp_user["user_id"] == user_id) & (sp_user["sp"] == species))]
            bot.send_message(user_id, "你已經選擇了: %s" % "、".join(list(sp_user[sp_user["user_id"] == user_id]["sp"])))


def insert(update, context):
    global sp_user
    send = update.callback_query.data
    user_id = update.callback_query.message.chat.id
    observer = update.callback_query.message.chat.username
    dt = datetime.datetime.strptime(str(update.callback_query.message.date)[:-6], "%Y-%m-%d %H:%M:%S") +datetime.timedelta(hours=8)

    if len(user_location[user_location['user_id'] == user_id].index) == 0:
        bot.send_message(user_id, "請先分享一個點位!")
        return

    x = float(user_location.loc[user_location['user_id'] == user_id]['x'].values)
    y = float(user_location.loc[user_location['user_id'] == user_id]['y'].values)

    sp_user_db = sp_user[sp_user['user_id'] == user_id]

    if send == "send":

        if len(sp_user_db.index) != 0:
            for index, row in sp_user_db.iterrows():
                print("%s, %s, %s, %s, %s, %s" % (row["sp"], x, y, dt, observer, row["user_id"]))


            bot.send_message(user_id, "紀錄已經成功上傳! \n要繼續上傳紀錄的話\n請再分享一個新的點位")

        else:
            bot.send_message(user_id, "請至少輸入一種物種")

    elif send == "cancel":
        if len(sp_user_db.index) != 0:
            sp_user = sp_user[sp_user["user_id"] != user_id]
            bot.send_message(user_id, "請重新選擇點位")


updater = Updater('1939444551:AAHoj_SazIr6Hpif3ZGi4uv5RWPnX3HOPBo')
updater.dispatcher.add_handler(MessageHandler(Filters.location, start))
updater.dispatcher.add_handler(MessageHandler(Filters.text, report))
updater.dispatcher.add_handler(CallbackQueryHandler(insert))
updater.start_polling()
updater.idle()