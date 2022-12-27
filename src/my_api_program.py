import requests

# Initialize
API_key = 'RGAPI-93acbca8-5216-47ea-8334-786afd569b78'
API_url = 'https://eun1.api.riotgames.com/lol/summoner/v4/summoners/by-name/TheStelinator'

API_url = f'{API_url}?api_key={API_key}'
print(requests.get(API_url))