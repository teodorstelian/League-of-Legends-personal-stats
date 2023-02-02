import requests
import settings

# Settings import
api_key = settings.API
summoner_name = settings.SUMMONER_NAME
region = settings.REGION

# Get the summoner's account ID
summoner_url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={api_key}"
summoner_response = requests.get(summoner_url)
summoner_data = summoner_response.json()
account_id = summoner_data["id"]

# Get the champion masteries for the player
masteries_url = f"https://{region}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/{account_id}?api_key={api_key}"
masteries_response = requests.get(masteries_url)
masteries_data = masteries_response.json()

# Print the champion masteries for the player
for mastery in masteries_data:
    champion_id = mastery["championId"]
    champion_level = mastery["championLevel"]
    champion_points = mastery["championPoints"]
    print(f"Champion ID: {champion_id} | Level: {champion_level} | Points: {champion_points}")