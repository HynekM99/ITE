import paho.mqtt.client as mqtt
import statistics as st
import json
import os.path
import re
import asyncio
import websockets

from threading import Timer
from datetime import datetime

SERVER = '147.228.124.230'  # RPi
TOPIC = 'ite/#'

team_names = ["black", "blue", "green", "orange", "pink", "red", "yellow"]
stats = ["prumerna", "median", "maximalni", "minimalni", "posledni"]

dict_data = {}
dict_timeMarks = {}

def getDate(str_createdOn):
    list_temp = str_createdOn.split("T")
    list_date = list_temp[0].split("-")
    return list_date

def getActDayListTemps(List_timeMarks):
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    list_temps = []

    for item_TM in List_timeMarks.items():
        date = getDate(item_TM[0])
        if ((date[0] == year) and (date[1] == month) and (date[2] == day)):
            list_temps.append(item_TM[1])
    return list_temps

def getStatistic(stat, data):
    if stat == "prumerna":
        return st.mean(data)
    elif stat == "median":
        return st.median(data)
    elif stat == "maximalni":
        return max(data)
    elif stat == "minimalni":
        return min(data)
    elif stat == "posledni":
        return data[-1]
    else:
        return None

def statistics(List_timeMarks):
    global stats
    dict_stat = {}
    tempList = getActDayListTemps(List_timeMarks)

    for stat in stats:
        if len(tempList) >= 1:
            dict_stat[stat] = '%0.1f' % round(getStatistic(stat, tempList), 1)
        else:
            dict_stat[stat] = "No data"

    return dict_stat

def on_connect(client, userdata, mid, qos):
    print('Connected with result code qos:', str(qos))
    client.subscribe(TOPIC)

def getCorrectData(stringReceived):
    stringReceived = stringReceived[1:-1]
    dataSeparated = stringReceived.split()
    
    correctData = {}
    correctData["source"] = "fake"
    correctData["team_name"] = dataSeparated[3][1:-2]
    correctData["created_on"] = fixTime(dataSeparated[5][1:-9])
    correctData["temperature"] = float(re.sub(r'[a-zA-Z]', '.', dataSeparated[7]))
    
    return correctData

def fixTime(time):
    fixes = {4: "-", 7: "-", 13: ":", 16: ":"}
    for key, item in fixes.items():
        time = time[:key] + item + time[key+1:]
    return time

def on_message(client, userdata, msg):
    global team_names, dict_data, dict_timeMarks

    if (msg.payload == 'Q'):
        client.disconnect()

    dict_msg_str = str(msg.payload.decode("utf-8","ignore"))
    print(dict_msg_str)

    try:
        dict_msg = getCorrectData(dict_msg_str)
        print(json.dumps(dict_msg)+"\n")
    except:
        print("An error occured while trying to repair data")
        return

    team = dict_msg["team_name"]
    if team in team_names:
        dict_timeMarks[team][dict_msg["created_on"]] = dict_msg["temperature"]
        dict_data[team] = statistics(dict_timeMarks[team])
        dict_data[team]["cas"] = getLastUpdateTime(team)
        dict_data[team]["online"] = True

        writeToFile("./Webovka/assets/data.json", json.dumps(dict_data, indent = 4))
        writeToFile("./temperatures/"+team+".json", json.dumps(dict_timeMarks[team], indent=4))

        asyncio.new_event_loop().run_until_complete(send_message("broadcast "+json.dumps(dict_data)))
        
async def send_message(message):
    address = 'ws://localhost:8881/websocket'
    try:
        async with websockets.connect(address) as ws:
            await ws.send(message)
    except:
        print("Could not establish connection with address "+address)

def writeToFile(path, data):
    try:
        with open(path, "w+") as f:
            f.write(data)
            f.close()
    except:
        print("An error occured while trying to write to json file")

def readDataFromJson(path):
    data = None
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
            f.close()
    except:
        print("An error occured while trying to read data from file "+path)

    return data

def getStoredDict(dictionary):
    if dictionary == None:
        return {}
    else:
        return dictionary

def getLastUpdateTime(team):
    last_time = list(dict_timeMarks[team].keys())[-1]
    if last_time == None:
        return "No data"
    else:
        return last_time

def main():
    global team_names, dict_timeMarks

    for team in team_names:
        dict_timeMarks[team] = getStoredDict(readDataFromJson("./temperatures/"+team+".json"))
        dict_data[team] = statistics(dict_timeMarks[team])
        dict_data[team]["cas"] = getLastUpdateTime(team)
        dict_data[team]["online"] = False
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set('mqtt_student', password='pivo')
    client.connect(SERVER, 1883, 60)
    client.loop_forever()


if __name__ == '__main__':
    main()