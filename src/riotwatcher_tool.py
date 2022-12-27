# Imports
from riotwatcher import LolWatcher

# Initialize
API_key = 'RGAPI-93acbca8-5216-47ea-8334-786afd569b78'
watcher = LolWatcher(API_key)
region = 'EUN1'
summoner_name = 'TheStelinator'

summoner = watcher.summoner.by_name(region, summoner_name)

print(summoner['summonerLevel'])

# all objects are returned (by default) as a dict
# lets see if i got diamond yet (i probably didnt)
my_ranked_stats = watcher.league.by_summoner(region, summoner['id'])
print(my_ranked_stats[0]['queueType'], my_ranked_stats[0]['tier'], my_ranked_stats[0]['rank'])


# # First we get the latest version of the game from data dragon
# versions = watcher.data_dragon.versions_for_region(region)
# champions_version = versions['n']['champion']
#
# # Lets get some champions
# current_champ_list = watcher.data_dragon.champions(champions_version)
# print(current_champ_list)
