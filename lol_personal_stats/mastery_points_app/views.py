# views.py
import requests
from django.conf import settings
from django.shortcuts import render

from .champion import Champion
from .summoner import Summoner


def index(request):
    return render(request, 'base.html', None)


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
        champion_level = champion["championLevel"]
        champion_name = all_champions.retrieve_id_and_name().get(str(champion_id), "Unknown")
        search_query = request.GET.get('champion_name', '')
        if search_query in champion_name and search_query == champion_name:
            mastery_points = {champion_name: [champion['championPoints'], champion_level]}
            break
        mastery_points[champion_name] = [champion['championPoints'], champion_level]
    return render(request, 'champion_mastery.html', {'mastery_points': mastery_points})


def get_match_history(request):
    # Settings import
    api_key = settings.API
    summoner_name = settings.SUMMONER_NAME
    region = settings.REGION

    # Get the summoner mastery data
    summoner = Summoner(region, api_key, summoner_name)

    for match in summoner.get_matches():
        matches_list = match['matches']
    return render(request, 'match_history.html', matches_list)
