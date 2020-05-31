import paho.mqtt.client as mqtt
import statistics as st
import websockets
import logging
import asyncio
import os.path
import json
import time
import re

from datetime import datetime
from threading import Timer
from rest_api import RestAPI

logging.getLogger('mqtt').setLevel(logging.WARNING)
logging.getLogger('websockets').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.basicConfig(
    format='%(asctime)s: [%(levelname)s] - %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S',
    filename='./logs/mqtt-log.log',
    level=logging.WARNING)


class MQTTSub:
    """
    Třída starající se o příjem, opravu a export teplotních dat.

    Parametry:
        rest -- instance třídy RestAPI
        server -- IP adresa brokeru
        topic -- topic, ze kterého je odebírán obsah brokeru
        teams -- názvy všech týmů
        stats -- požadované statistiky
    """
    SERVER = '147.228.124.230'
    TOPIC = 'ite/#'
    TEAM_NAMES = ["black", "blue", "green", "orange", "pink", "red", "yellow"]
    STATS = ["prumerna", "maximalni", "minimalni", "posledni"]

    dict_data = {}
    # Klíče jsou názvy týmů.
    # Každý klíč obsahuje další slovník, jehož klíče jsou názvy statistik.

    dict_measurements = {}
    # Klíč -- název týmu.
    # Hodnota -- slovník přijatých teplotních záznamů
    # Hodnota -- {'čas1': teplota1, 'čas2': teplota2,...}.

    server_status = False
    rest = None

    def __init__(self, rest, server, topic, teams, stats):
        self.rest = rest
        self.SERVER = server
        self.TOPIC = topic
        self.TEAM_NAMES = teams
        self.STATS = stats

    def start(self):
        """ Načte a zpracuje dnešní naměřené hodnoty,
        připojí se k centrálnímu brokeru a dále přijímá
        a zpracovává data.
        """
        for team in self.TEAM_NAMES:
            team_stats_file = "./temperatures/"+team+".json"
            team_measurements = self.read_from_json("./temperatures/"+team+".json")
            today_measurements = self.get_today_measurements(team_measurements)
            self.dict_measurements[team] = today_measurements

            self.dict_data[team] = self.statistics(self.dict_measurements[team])
            self.dict_data[team]["cas"] = self.get_last_update(team)
            self.dict_data[team]["online"] = False

        self.server_status = self.rest.login()
        asyncio.new_event_loop().run_until_complete(
            self.send_message("server "+str(self.server_status).lower()))

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set('mqtt_student', password='pivo')
        self.client.connect(self.SERVER, 1883, 60)
        self.client.loop_forever()

    def on_connect(self, client, userdata, mid, qos):
        logging.info('Connected with result code qos:'+str(qos))
        self.client.subscribe(self.TOPIC)

    def on_message(self, client, userdata, msg):
        if (msg.payload == 'Q'):
            client.disconnect()

        dict_msg_str = str(msg.payload.decode("utf-8", "ignore"))
        logging.info('<- '+dict_msg_str)

        try:
            dict_msg = self.get_correct_data(dict_msg_str)
        except Exception as e:
            logging.exception("An error occured while trying to repair data")
            return
        else:
            if not self.test_data(dict_msg):
                logging.error("Repaired data contained a mistake")
                return

        team = dict_msg["team_name"]
        if team in self.TEAM_NAMES:
            created_on = dict_msg["created_on"]
            temperature = dict_msg["temperature"]
            self.dict_measurements[team][created_on] = temperature

            all_measurements = self.dict_measurements[team]
            today_measurements = self.get_today_measurements(all_measurements)
            self.dict_measurements[team] = today_measurements

            self.dict_data[team] = self.statistics(self.dict_measurements[team])
            self.dict_data[team]["cas"] = self.get_last_update(team)
            self.dict_data[team]["online"] = True

            team_data = {}
            team_data[team] = self.dict_data[team]

            stats_file = "./assets/data.json"
            all_stats = json.dumps(self.dict_data, indent=4)

            self.write_to_file(stats_file, all_stats)

            team_measurements_file = "./temperatures/"+team+".json"
            team_measurements = json.dumps(self.dict_measurements[team], indent=4)

            self.write_to_file(team_measurements_file, team_measurements)

            asyncio.new_event_loop().run_until_complete(
                self.send_message("broadcast "+json.dumps(team_data)))

            if team == "red":
                for i in range(2):
                    # Cyklus, ktery probehne 2x, kvuli obcasnemu timeoutu.
                    self.server_status = self.rest.login()
                    if self.server_status:
                        created_on = dict_msg["created_on"]+".000+02:00"
                        temperature = round(dict_msg["temperature"], 1)
                        self.rest.create_measurement(
                            created_on, temperature, "OK")
                        break

            asyncio.new_event_loop().run_until_complete(
                    self.send_message("server "+str(server_status).lower()))

        else:
            logging.info("Data arrived for unknown team: "+team)

    def get_correct_data(self, string_received):
        """ Metoda opravuje přijatá data z brokeru na základě empiricky
        zjištěného principu výskytu chyb.

        Parametr:
            string_received -- Řetezec, reprezentující zprávu z brokeru
        """
        string_received = string_received[1:-1]
        data_separated = string_received.split()

        fixed_time = self.fix_time(data_separated[5][1:-9])
        fixed_temperature = float(re.sub(r'[A-Za-z]', '.', data_separated[7]))

        correctData = {}
        correctData["source"] = "fake"
        correctData["team_name"] = data_separated[3][1:-2]
        correctData["created_on"] = fixed_time
        correctData["temperature"] = fixed_temperature

        return correctData

    def statistics(self, team_measurements):
        """ Vypočítá všechny statistiky ze zadaných dat.

        Parametry:
            team_measurements -- Slovník teplotních záznamů
        """
        dict_stat = {}
        temperatures = list(team_measurements.values())

        for stat in self.STATS:
            if temperatures:
                stat_value = round(self.get_statistic(stat, temperatures), 1)
                dict_stat[stat] = '%0.1f' % stat_value
            else:
                dict_stat[stat] = "No data"

        return dict_stat

    def test_data(self, data):
        """ Testuje, zda je v zadaném slovníku čas a teplota měření
        ve správném formátu.

        Parametr:
            data -- Slovník s opravenými daty
        """
        date_correct = self.test_date(data["created_on"])
        temp_correct = self.test_temperature(data["temperature"])
        data_correct = date_correct and temp_correct
        return data_correct

    def test_date(self, created_on):
        """ Testuje, zda je čas zprávy ve správném formátu
        a neobsahuje nepřípustné znaky.

        Parametr:
            created_on -- Řetězec, který reprezentuje čas.
        """
        try:
            date_time = created_on.split("T")
            list_date = date_time[0].split("-")
            list_time = date_time[1].split(":")
            list_date.extend(list_time)

            for num in list_date:
                try:
                    int(num)
                except Exception as e:
                    return False
        except Exception as e:
            return False
        else:
            return True

    def test_temperature(self, temperature):
        """ Testuje, zda je teplota ve zprávě ve správném formátu
        a neobsahuje nepřípustné znaky.

        Parametr:
            temperature -- Reálné číslo.
        """
        try:
            float(temperature)
        except Exception as e:
            return False
        else:
            return True

    def get_last_update(self, team):
        """ Vrací ze seznamu časových známek měření poslední hodnotu,
        pokud není seznam prázdný. Pokud je prázdný, vrací řetězec "No data".

        Parametr:
        team -- řetězec, reprezentující daný tým
        """
        if not list(self.dict_measurements[team].keys()):
            return "No data"
        return list(self.dict_measurements[team].keys())[-1]

    def get_date_list(self, created_on):
        """ Ze zadaného času vytvoří seznam
        se všemi jeho datovými a časovými hodnotami.

        Parametr:
            created_on -- Řetězec, reprezentující datum a čas
        """
        date_time = created_on.split("T")
        list_date = date_time[0].split("-")
        return list_date

    def get_today_measurements(self, team_measurements):
        """ Vrací slovník s naměřenými hodnotami z aktuálního dne.

        Parametr:
            team_measurements -- Seznam naměřených hodnot
        """
        if team_measurements is None:
            return {}

        now = datetime.now()

        year = str(now.strftime("%Y"))
        month = str(now.strftime("%m"))
        day = str(now.strftime("%d"))
        today_measurements = {}

        for item in team_measurements.items():
            date = self.get_date_list(item[0])
            if date[0] == year and date[1] == month and date[2] == day:
                today_measurements[item[0]] = item[1]

        return today_measurements

    def get_statistic(self, stat, data):
        """ Vypočítá zadanou statistiku z poskytnutých dat.

        Parametry:
            stat -- Řetězec, reprezentující statistiku
            data -- Seznam teplot
        """
        if stat == "prumerna":
            return st.mean(data)
        elif stat == "maximalni":
            return max(data)
        elif stat == "minimalni":
            return min(data)
        elif stat == "posledni":
            return data[-1]
        else:
            return None

    def fix_time(self, time):
        """ Opravuje čas na požadovaný tvar.

        Parametr:
            time -- Hodnota, příslušící klíči "created_on" ve zprávě z brokeru
        """
        fixes = {4: "-", 7: "-", 10: "T", 13: ":", 16: ":"}
        for key, item in fixes.items():
            time = time[:key] + item + time[key+1:]
        return time

    async def send_message(self, message):
        """ Asynchronní metoda pro odeslání zprávy lokálnímu webserveru.

        Parametry:
            message -- Zpráva k odeslání
        """
        address = 'ws://localhost:8881/websocket'
        try:
            async with websockets.connect(address) as ws:
                await ws.send(message)
        except Exception as e:
            logging.exception("Could not connect to webserver")

    def write_to_file(self, path, data):
        """ Zapisuje data do souboru.

        Parametr:
            path -- cesta k souboru
            data -- data, která chci zapsat
        """
        try:
            with open(path, "w+") as f:
                f.write(data)
                f.close()

        except Exception as e:
            logging.exception("Could not write data to file "+path)

    def read_from_json(self, path):
        """ Čte data ze souboru.

        Parametr:
            path -- cesta k souboru
        """
        data = None
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r") as f:
                data = json.load(f)
                f.close()
        except Exception as e:
            logging.exception("Could not read data from file "+path)

        return data


if __name__ == '__main__':
    username = "Red"  # Uživatelské jméno pro API.
    password = "RX8u!dZQ"  # Heslo pro API.
    rest = RestAPI(username, password)
    server = '147.228.124.230'  # IP adresa brokeru.
    topic = 'ite/#'  # Topic, ze ktereho je odebiran obsah brokeru.
    teams = ["black", "blue", "green", "orange", "pink", "red", "yellow"]
    stats = ["prumerna", "maximalni", "minimalni", "posledni"]

    mqtt_subscriber = MQTTSub(
        rest=rest,
        server=server,
        topic=topic,
        teams=teams,
        stats=stats,
        )
    mqtt_subscriber.start()
