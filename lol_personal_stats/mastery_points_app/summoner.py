import requests


class Summoner:

    def __init__(self, region, api_key, summoner_name):
        self.api_key = api_key
        self.id = None
        self.region = region
        self.summoner_name = summoner_name

    def get_id(self):
        """
            Get the summoner's account ID
        """
        summoner_url = f"https://{self.region}.api.riotgames.com" \
                       f"/lol/summoner/v4/summoners/by-name/{self.summoner_name}?api_key={self.api_key}"
        summoner_response = requests.get(summoner_url)
        summoner_data = summoner_response.json()
        print(summoner_data)
        self.id = summoner_data["id"]

    def get_masteries(self):
        """
            Get the masteries points of a specific summoner
        """
        self.get_id()
        # Get the champion masteries for the player
        masteries_url = f"https://{self.region}.api.riotgames.com/lol/champion-mastery/" \
                        f"v4/champion-masteries/by-summoner/{self.id}?api_key={self.api_key}"
        masteries_response = requests.get(masteries_url)
        return masteries_response.json()
