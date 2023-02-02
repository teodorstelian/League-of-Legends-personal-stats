import requests
import settings
from champion import Champion
from summoner import Summoner

# Settings import
api_key = settings.API
summoner_name = settings.SUMMONER_NAME
region = settings.REGION

# Get the champion names for the respective id
champion = Champion()

# Get the summoner mastery data
summoner = Summoner(region, api_key, summoner_name)

# Print the champion masteries for the player, using the champion name instead of the ID
for mastery in summoner.get_masteries():
    champion_id = mastery["championId"]
    champion_level = mastery["championLevel"]
    champion_points = mastery["championPoints"]
    champion_name = champion.retrieve_id_and_name().get(str(champion_id), "Unknown")
    print(f"Champion Name: {champion_name} | Level: {champion_level} | Points: {champion_points}")
