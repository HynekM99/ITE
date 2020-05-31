import urllib.request
import logging
import json


class RestAPI:
    '''
    Třída pro obsluhu rozhraní REST API

    Parameters:
        username (string): Název týmu
        password (string): Heslo týmu
    '''
    USERNAME = ""
    PASSWORD = ""
    server_url = "https://uvb1bb4153.execute-api.eu-central-1.amazonaws.com/Prod/"
    user_agent = "PostmanRuntime/7.24.1"
    content_type = "application/json"
    teamUUID = ""

    allowAlert = True

    def __init__(self, username, password):
        self.USERNAME = username
        self.PASSWORD = password

    def login(self):
        ''' Zavolá přihlašovací požadavek login a zaznamená ID týmu

        Returns:
            bool: Úspěšnost loginu
        '''

        headers = {
            "Content-Type": self.content_type,
            "User-Agent": self.user_agent
        }

        body = {
            "username": self.USERNAME,
            "password": self.PASSWORD
        }

        response = self.call_request(body, headers, "login")

        if response is None:
            return False
        if response["teamUUID"] is None:
            return False

        self.teamUUID = response["teamUUID"]
        return True

    def create_measurement(self, created_on, temperature, status):
        ''' Zavolá požadavek pro vytvoření záznamu o teplotě

        Parameters:
            created_on (string): Datum a čas naměření teploty
                (YYYY-MM-DDTHH:MM:SS.fffZ)
            temperature (float): Naměřená teplota
            status (string): OK

        Returns:
            dict: Informace o záznamu
        '''

        sensor = self.get_sensors(self.teamUUID)[0]
        sensorUUID = sensor["sensorUUID"]
        sensorMaxTemp = sensor["maxTemperature"]
        sensorMinTemp = sensor["minTemperature"]

        if sensor is None:
            return None

        headers = {
            "Content-Type": self.content_type,
            "User-Agent": self.user_agent,
            "teamUUID": self.teamUUID
        }

        body = {
            "createdOn": created_on,
            "sensorUUID": sensorUUID,
            "temperature": str(temperature),
            "status": status
        }

        response = self.call_request(body, headers, "measurements")

        if response is None:
            return None
        if response["message"] != "Measurement stored!":
            return None

        if temperature > sensorMaxTemp or temperature < sensorMinTemp:
            if self.allowAlert:
                self.allowAlert = False
                self.create_alert(
                    created_on,
                    sensorUUID,
                    temperature,
                    sensorMaxTemp,
                    sensorMinTemp
                    )
        else:
            self.allowAlert = True

        return response

    def get_sensors(self, teamUUID):
        ''' Zavolá požadavek pro zjištění informací o senzorech týmu

        Parameters:
            teamUUID (string): ID týmu

        Returns:
            dict: Informace o senzorech týmu
        '''

        headers = {
            "teamUUID": teamUUID,
            "User-Agent": self.user_agent
        }

        body = None

        response = self.call_request(body, headers, "sensors")

        if response is None:
            return None
        if response[0]["sensorUUID"] is None:
            return None

        return response

    def create_alert(self, created_on, sensorUUID, temperature, high_temperature, low_temperature):
        ''' Zavolá požadavek pro vytvořeni alertu

        Parameters:
            created_on (string): Datum a čas naměření teploty
                (YYYY-MM-DDTHH:MM:SS.fffZ)
            sensorUUID (string): ID senzoru
            temperature (float): Naměřená teplota
            high_temperature (float): Horní mez pro vyvolání alertu
            low_temperature (float): Dolní mez pro vyvolání alertu

        Returns:
            dict: Informace o záznamu alertu
        '''

        headers = {
            "Content-Type": self.content_type,
            "User-Agent": self.user_agent,
            "teamUUID": self.teamUUID
        }

        body = {
            "createdOn": created_on,
            "sensorUUID": sensorUUID,
            "temperature": temperature,
            "highTemperature": high_temperature,
            "lowTemperature": low_temperature
        }

        response = self.call_request(body, headers, "alerts")

        if response is None:
            return None
        if response["message"] != "Alert stored!":
            return None

        return response

    def call_request(self, body, headers, request_type):
        ''' Zavolá zadaný požadavek s hlavičkami a tělem

        Parameters:
            body (dict): Tělo požadavku
            headers (dict): Hlavičky požadavku
            request_type (dict): Typ požadavku

        Returns:
            dict: Informace získané z požadavku
        '''
        url = self.server_url+request_type
        url_request = urllib.request.Request(url, headers=headers)
        response = None

        try:
            if body is None:
                response = urllib.request.urlopen(url_request)
            else:
                str_body = json.dumps(body).encode('utf-8')
                response = urllib.request.urlopen(url_request, str_body)
            logging.info("URL request successful: "+request_type)
        except Exception as e:
            logging.exception(
                "An error occured while calling url request "+request_type)
            return None

        data_received = response.read()
        data = json.loads(data_received.decode('utf-8'))
        return data
