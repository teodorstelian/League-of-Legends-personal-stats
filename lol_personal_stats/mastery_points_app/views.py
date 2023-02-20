# views.py
from django.shortcuts import render
from django.conf import settings

from .champion import Champion
from .summoner import Summoner


def champion_mastery(request):

    # Settings import
    api_key = settings.API
    summoner_name = settings.SUMMONER_NAME
    region = settings.REGION

    # Get the champion names for the respective id
    all_champions = Champion()

    # Get the summoner mastery data
    summoner = Summoner(region, api_key, summoner_name)

    # Print the champion masteries for the player, using the champion name instead of the ID
    mastery_points = {}
    for champion in summoner.get_masteries():
        champion_id = champion["championId"]
        champion_name = all_champions.retrieve_id_and_name().get(str(champion_id), "Unknown")
        mastery_points[champion_name] = champion['championPoints']
    return render(request, 'champion_mastery.html', {'mastery_points': mastery_points})
