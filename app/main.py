import asyncio
import os
import time
from contextlib import asynccontextmanager
from typing import Literal
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
cache = {}
lock = asyncio.Lock()


class RiotError(Exception):
    def __init__(self, message, status=502):
        self.message, self.status = message, status


@asynccontextmanager
async def lifespan(app):
    async with httpx.AsyncClient(timeout=15) as client:
        app.state.client = client
        yield


app = FastAPI(title="Rift Journal", lifespan=lifespan)
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')


@app.get('/')
async def home():
    return FileResponse(ROOT / 'static/index.html')


async def fetch(client, url, key=None):
    try:
        response = await client.get(url, headers={'X-Riot-Token': key} if key else {})
    except httpx.RequestError:
        raise RiotError('Unable to reach Riot. Please try again shortly.') from None
    if response.status_code in (401, 403):
        raise RiotError('Riot rejected the API key. Update RIOT_API_KEY in .env; development keys expire.', 503)
    if response.status_code == 404:
        raise RiotError('Player or game data was not found. Check your Riot ID and EUNE account.', 404)
    if response.status_code == 429:
        retry = response.headers.get('Retry-After', 'a few')
        raise RiotError(f'Riot rate limit reached. Try again in {retry} seconds.', 429)
    if not response.is_success:
        raise RiotError('Riot is temporarily unavailable. Please try again later.')
    try:
        return response.json()
    except ValueError:
        raise RiotError('Riot returned an unexpected response. Please try again.') from None


def match_summary(match, puuid):
    info = match['info']
    player = next((p for p in info['participants'] if p['puuid'] == puuid), None)
    if not player:
        return None
    duration = info.get('gameDuration', 0)
    return {
        'id': match['metadata']['matchId'], 'champion': player['championName'],
        'championId': player['championId'], 'win': player['win'],
        'kills': player['kills'], 'deaths': player['deaths'], 'assists': player['assists'],
        'cs': player.get('totalMinionsKilled', 0) + player.get('neutralMinionsKilled', 0),
        'duration': duration, 'mode': info.get('gameMode', 'Unknown'),
        'queue': info.get('queueId'), 'playedAt': info.get('gameStartTimestamp', 0),
    }


QUEUES = {'all': None, 'solo': 420, 'flex': 440, 'aram': 450}


async def dashboard(client, key, riot_id, queue='all'):
    name, tag = riot_id.rsplit('#', 1)
    regional = 'https://europe.api.riotgames.com'
    platform = 'https://eun1.api.riotgames.com'
    account = await fetch(client, f'{regional}/riot/account/v1/accounts/by-riot-id/{quote(name, safe="")}/{quote(tag, safe="")}', key)
    puuid = quote(account['puuid'], safe='')
    profile = await fetch(client, f'{platform}/lol/summoner/v4/summoners/by-puuid/{puuid}', key)
    masteries = await fetch(client, f'{platform}/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}', key)
    ranked, rank_warning = None, None
    try:
        entries = await fetch(client, f'{platform}/lol/league/v4/entries/by-puuid/{puuid}', key)
        ranked = []
        for queue_type, label in [('RANKED_SOLO_5x5', 'Solo / Duo'), ('RANKED_FLEX_SR', 'Flex')]:
            entry = next((e for e in entries if e['queueType'] == queue_type), None)
            ranked.append({'queue': label, 'tier': entry['tier'] if entry else None,
                           'division': entry['rank'] if entry else None,
                           'lp': entry['leaguePoints'] if entry else None,
                           'wins': entry['wins'] if entry else 0,
                           'losses': entry['losses'] if entry else 0})
    except RiotError as exc:
        rank_warning = exc.message
    queue_query = f'&queue={QUEUES[queue]}' if QUEUES[queue] else ''
    ids = await fetch(client, f'{regional}/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=10{queue_query}', key)
    # Sequential match calls avoid a burst against the development key's short rate window.
    matches, warning = [], None
    for match_id in ids:
        try:
            match = await fetch(client, f'{regional}/lol/match/v5/matches/{quote(match_id, safe="")}', key)
            summary = match_summary(match, account['puuid'])
            if summary:
                matches.append(summary)
        except RiotError as exc:
            warning = exc.message
            break
    now = time.monotonic()
    if 'champions' not in cache or cache['champions'][0] < now:
        versions = await fetch(client, 'https://ddragon.leagueoflegends.com/api/versions.json')
        version = versions[0]
        data = await fetch(client, f'https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json')
        cache['champions'] = (now + 21600, version, {int(c['key']): c for c in data['data'].values()})
    _, version, champions = cache['champions']
    def champion_data(champion_id):
        c = champions.get(champion_id)
        return {'name': c['name'] if c else f'Champion {champion_id}',
                'icon': f'https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{c["image"]["full"]}' if c else None}
    mastery = [{**champion_data(m['championId']), 'points': m['championPoints'], 'level': m['championLevel']} for m in masteries]
    mastery.sort(key=lambda m: m['points'], reverse=True)
    for match in matches:
        match.update(champion_data(match['championId']))
    return {'riotId': f'{account.get("gameName", name)}#{account.get("tagLine", tag)}',
            'region': 'EUNE', 'level': profile['summonerLevel'],
            'icon': f'https://ddragon.leagueoflegends.com/cdn/{version}/img/profileicon/{profile["profileIconId"]}.png',
            'mastery': mastery, 'matches': matches, 'warning': warning,
            'ranked': ranked, 'rankWarning': rank_warning, 'queue': queue,
            'updatedAt': int(time.time())}


@app.get('/api/dashboard')
async def get_dashboard(queue: Literal['all', 'solo', 'flex', 'aram'] = 'all'):
    load_dotenv(ROOT / '.env', override=True)
    key = os.getenv('RIOT_API_KEY', '').strip()
    riot_id = os.getenv('RIOT_ID', 'Bagabondu#1909').strip()
    if not key:
        return JSONResponse({'message': 'Add your Riot API key to RIOT_API_KEY in the .env file, then click Refresh.', 'setup': True}, status_code=503)
    if '#' not in riot_id or not all(riot_id.rsplit('#', 1)):
        return JSONResponse({'message': 'RIOT_ID must include both name and tagline, for example Bagabondu#1909.'}, status_code=400)
    async with lock:
        cache_key = ('dashboard', queue)
        cached = cache.get(cache_key)
        if cached and cached[0] > time.monotonic() and cached[1:3] == (key, riot_id):
            return cached[3]
        try:
            data = await dashboard(app.state.client, key, riot_id, queue)
        except RiotError as exc:
            return JSONResponse({'message': exc.message}, status_code=exc.status)
        cache[cache_key] = (time.monotonic() + 120, key, riot_id, data)
        return data
