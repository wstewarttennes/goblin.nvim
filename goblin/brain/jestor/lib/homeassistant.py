import os, requests

class HomeAssistantApi():

    def __init__(self):
        self.TOKEN = os.environ.get("HOMEASSISTANT_TOKEN")
        self.url = "http://dijondreams:8123/api/"
        self.headers = {
            "Authorization": f"Bearer {self.TOKEN}",
            "content-type": "application/json",
        }

    def get_request(self, url, params):
        res = requests.get(self.url + url, params)
        return res



