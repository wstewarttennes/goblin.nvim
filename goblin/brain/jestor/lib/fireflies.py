import os
import requests

class FirefliesApi():

    def __init__(self):
        self.URL = 'https://api.fireflies.ai/graphql'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + os.environ.get("FIREFLIES_API_KEY", "")
        }

    
    def get_users(self):
        data = {
            'query': '{ users { name user_id } }'
        }
        response = requests.post(self.URL, json=data, headers=self.headers)
        return response.json()

    def get_meeting(self, meeting_id):
        pass

    def get_meetings(self, filter):
        pass

