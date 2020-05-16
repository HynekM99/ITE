import paho.mqtt.client as mqtt
import statistics as st
import json
import os.path
import re

my_path = 'D:\KKY\ITE\SP\ITE-master\Webovka\assets'
SERVER = '147.228.124.230'  # RPi
TOPIC = 'ite/#'
#list dat i.e. blue = [[list_teplot], posledni, prumer, median, nejvyssi, nejnizsi, ]
list_blueTmprs = []
list_greenTmprs = []
list_pinkTmprs = []
list_redTmprs = []
list_blackTmprs = []
list_orangeTmprs = []
list_yellowTmprs = []

list_blueStat = []
list_greenStat = []
list_pinkStat = []
list_redStat = []
list_blackStat = []
list_orangeStat = []
list_yellowStat = []


def getTime(time):
    list_created_on = time.split("T")
    list_date = list_created_on[0].split("-")
    list_date = list_date[::-1]
    str_created_on = list_created_on[1] + " " + list_date[0] + "."+  list_date[1] + "." +  list_date[2]
    return str_created_on

def statistics_(tempList):
    if len(tempList) >= 1:
        list_stat =  [st.mean(tempList), st.median(tempList), max(tempList), min(tempList), tempList[len(tempList)-1]]
        lis_statRound = [round(x,1) for x in list_stat]
        return lis_statRound
    else:
        return ['No data','No data','No data','No data','No data']
    
def on_connect(client, userdata, mid, qos):
    print('Connected with result code qos:', str(qos))
    client.subscribe(TOPIC)

    
def team(dict):
    team_name = dict['team_name']
    return team_name

def getCorrectData(stringReceived):
    stringReceived.replace('\'', '\"')
    stringReceived = stringReceived[1:len(stringReceived)]
    dataSeparated = stringReceived.split()
    
    correctDataList = ['"source"', '"fake"', '"team_name"']
    correctDataList.append('"'+dataSeparated[3][1:-2]+'"')
    correctDataList.append('"created_on"')
    correctDataList.append('"'+fixTime(dataSeparated[5][1:-2])+'"')
    correctDataList.append('"temperature"')
    correctDataList.append(re.sub(r'[a-zA-Z]', '.', dataSeparated[7][:-1]))
    
    return listToJsonString(correctDataList)

def listToJsonString(dataList):
    jsonString = "{"
    for i in range(0, len(dataList), 2):
        jsonString += dataList[i]+": "+dataList[i+1]
        if i+2 < len(dataList):
            jsonString += ", "
    jsonString += "}"
    return jsonString

def fixTime(time):
    fixes = {4: "-", 7: "-", 13: ":", 16: ":", 19: "."}
    for key, item in fixes.items():
        time = time[:key] + item + time[key+1:]
    return time

def on_message(client, userdata, msg):
    global list_blueTmprs, list_greenTmprs, list_pinkTmprs, list_redTmprs, list_blackTmprs, list_orangeTmprs, list_yellowTmprs
    global list_blueStat, list_greenStat, list_pinkStat, list_redStat, list_blackStat, list_orangeStat, list_yellowStat
    global time_blue, time_black, time_pink, time_red, time_orange, time_yellow
    
    if (msg.payload == 'Q'):
        client.disconnect()

    dict_msg_str = str(msg.payload.decode("utf-8","ignore"))
    print(dict_msg_str)

    dict_msg_rep = getCorrectData(dict_msg_str)
    print(dict_msg_rep+"\n")
    
    try:
        dict_msg = json.loads(dict_msg_rep)  # vraci slovnik, parametr je json file
    except Exception:
        print("Incorrect data")
        return
        
    if (team(dict_msg) == "blue"):
        list_blueTmprs.append(dict_msg["temperature"])
        time_blue = getTime(dict_msg["created_on"])
        
    if (team(dict_msg) == "black"):
        list_blackTmprs.append(dict_msg["temperature"])
        time_black = dict_msg["created_on"]
            
    if (team(dict_msg) == "pink"):
        list_pinkTmprs.append(dict_msg["temperature"])
        time_pink = getTime(dict_msg["created_on"])
            
    if (team(dict_msg) == "red"):
        list_redTmprs.append(dict_msg["temperature"])
        time_red = getTime(dict_msg["created_on"])
            
    if (team(dict_msg) == "orange"):
        list_orangeTmprs.append(dict_msg["temperature"])
        time_orange = getTime(dict_msg["created_on"])
            
    if (team(dict_msg) == "yellow"):
        list_yellowTmprs.append(dict_msg["temperature"])
        time_yellow = getTime(dict_msg["created_on"])
            
    if (team(dict_msg) == "green"):
        list_greenTmprs.append(dict_msg["temperature"])
        time_green = getTime(dict_msg["created_on"])
            
        
    dict_data = {"blue" : {"prumerna": statistics_(list_blueTmprs)[0],
                            "median" : statistics_(list_blueTmprs)[1],
                            "maximalni": statistics_(list_blueTmprs)[2],
                            "minimalni": statistics_(list_blueTmprs)[3],
                            "posledni": statistics_(list_blueTmprs)[4],
                            "cas": getTime(dict_msg["created_on"])},
                    
                    "green" : {"prumerna": statistics_(list_greenTmprs)[0],
                            "median" : statistics_(list_greenTmprs)[1],
                            "maximalni": statistics_(list_greenTmprs)[2],
                            "minimalni": statistics_(list_greenTmprs)[3],
                            "posledni": statistics_(list_greenTmprs)[4],
                            "cas":  getTime(dict_msg["created_on"])},
                    
                    "black" : {"prumerna": statistics_(list_blackTmprs)[0],
                            "median" : statistics_(list_blackTmprs)[1],
                            "maximalni": statistics_(list_blackTmprs)[2],
                            "minimalni": statistics_(list_blackTmprs)[3],
                            "posledni":  statistics_(list_blackTmprs)[4],
                            "cas":  getTime(dict_msg["created_on"])},
                    
                    "pink" : {"prumerna": statistics_(list_pinkTmprs)[0],
                            "median" : statistics_(list_pinkTmprs)[1],
                            "maximalni": statistics_(list_pinkTmprs)[2],
                            "minimalni": statistics_(list_pinkTmprs)[3],
                            "posledni":  statistics_(list_pinkTmprs)[4],
                            "cas":  getTime(dict_msg["created_on"])},
                    
                    "red" : {"prumerna": statistics_(list_redTmprs)[0],
                            "median" : statistics_(list_redTmprs)[1],
                            "maximalni": statistics_(list_redTmprs)[2],
                            "minimalni": statistics_(list_redTmprs)[3],
                            "posledni":  statistics_(list_redTmprs)[4],
                            "cas":  getTime(dict_msg["created_on"])},
                    
                    "orange" : {"prumerna": statistics_(list_orangeTmprs)[0],
                            "median" : statistics_(list_orangeTmprs)[1],
                            "maximalni": statistics_(list_orangeTmprs)[2],
                            "minimalni": statistics_(list_orangeTmprs)[3],
                            "posledni":  statistics_(list_orangeTmprs)[4],
                            "cas":  getTime(dict_msg["created_on"])},
                    
                    "yellow" : {"prumerna": statistics_(list_yellowTmprs)[0],
                            "median" : statistics_(list_yellowTmprs)[1],
                            "maximalni": statistics_(list_yellowTmprs)[2],
                            "minimalni": statistics_(list_yellowTmprs)[3],
                            "posledni":  statistics_(list_yellowTmprs)[4],
                            "cas":  getTime(dict_msg["created_on"])}}
                            
    json_file = json.dumps(dict_data, indent = 4)
    f2 = open("./Webovka/assets/data.json", "w+")  
    f2.write(json_file)   
    f2.close()
                                                                          

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set('mqtt_student', password='pivo')
    client.connect(SERVER, 1883, 60)
    client.loop_forever()


if __name__ == '__main__':
    main()