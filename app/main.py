import asyncio
import os
import time
import sqlite3
from contextlib import suppress
from contextlib import asynccontextmanager
from typing import Literal
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from . import storage
from .scoring import score_player
from .statistics import enrich_dashboard, score_average, lane_averages, champion_tiers
from .history_policy import eligible_info
from .trends import performance_trends

ROOT = Path(__file__).resolve().parent.parent
cache = {}
lock = asyncio.Lock()
request_lock = asyncio.Lock()
next_request = 0
sync_status = {'status': 'starting', 'message': ''}


def configuration():
    load_dotenv(ROOT / '.env', override=True)
    return os.getenv('RIOT_API_KEY', '').strip(), os.getenv('RIOT_ID', 'Bagabondu#1909').strip()


async def sync_worker(client):
    last_recent = {}
    last_profile = {}
    reset_recent = set()
    while True:
        key, player = configuration()
        state = storage.state(player)
        if player not in reset_recent:
            state['recent_offset'] = 0
            storage.save_state(player, state)
            reset_recent.add(player)
        try:
            if not key or state['paused']:
                sync_status.update(status='paused' if state['paused'] else 'setup', message='Sync paused.' if state['paused'] else 'Add your Riot API key.')
                await asyncio.sleep(2)
                continue
            saved = storage.matches(player)
            if time.monotonic() - last_profile.get(player, 0) > 300:
                profile = await dashboard(client, key, player)
                storage.profile(player, profile)
                last_profile[player] = time.monotonic()
            backfill = len(saved) < state['target'] and not state['exhausted']
            recent = time.monotonic() - last_recent.get(player, 0) > 300
            pending = storage.pending(player) if not backfill and not recent else []
            hydrate = bool(pending)
            if not backfill and not recent and not hydrate:
                sync_status.update(status='idle', message='Up to date. Checking for new games every 5 minutes.')
                await asyncio.sleep(2)
                continue
            sync_status.update(status='syncing', message='Checking new games…' if recent else 'Importing older games…')
            if hydrate:
                sync_status['message'] = 'Adding advanced details to saved matches…'
            name, tag = player.rsplit('#', 1)
            base = 'https://europe.api.riotgames.com'
            account = await fetch(client, f'{base}/riot/account/v1/accounts/by-riot-id/{quote(name, safe="")}/{quote(tag, safe="")}', key)
            puuid = quote(account['puuid'], safe='')
            # A fixed end timestamp keeps pagination stable as new games arrive.
            state.setdefault('end', int(time.time()))
            offset = state.get('recent_offset', 0) if recent else state['offset']
            suffix = '' if recent else f'&endTime={state["end"]}'
            ids = pending if hydrate else await fetch(client, f'{base}/lol/match/v5/matches/by-puuid/{puuid}/ids?start={offset}&count=20&type=ranked{suffix}', key)
            known = {m['id'] for m in saved}
            completed = True
            for match_id in ids:
                if storage.state(player)['paused']:
                    completed = False
                    break
                if match_id not in known or storage.detail(player, match_id) is None:
                    raw = await fetch(client, f'{base}/lol/match/v5/matches/{quote(match_id, safe="")}', key)
                    summary = match_summary(raw, account['puuid'])
                    if summary:
                        storage.save_match(player, summary)
                        storage.detail(player, match_id, {'raw': raw, 'puuid': account['puuid']})
            if completed:
                # Preserve controls changed while network requests were in progress.
                current = storage.state(player)
                current.setdefault('end', state['end'])
                if recent:
                    if not saved or not ids or any(mid in known for mid in ids) or len(ids) < 20:
                        last_recent[player] = time.monotonic()
                        current['recent_offset'] = 0
                    else:
                        current['recent_offset'] = offset + len(ids)
                elif not hydrate:
                    current['offset'] = offset + len(ids)
                    current['exhausted'] = len(ids) < 20
                storage.save_state(player, current)
        except RiotError as exc:
            sync_status.update(status='waiting', message=exc.message)
            await asyncio.sleep(30)
        except (ValueError, KeyError, TypeError, sqlite3.Error):
            sync_status.update(status='error', message='Unable to sync history. Check configuration and try resuming.')
            await asyncio.sleep(30)


class RiotError(Exception):
    def __init__(self, message, status=502):
        self.message, self.status = message, status


@asynccontextmanager
async def lifespan(app):
    storage.apply_history_policy()
    async with httpx.AsyncClient(timeout=15) as client:
        app.state.client = client
        task = asyncio.create_task(sync_worker(client))
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(title="Rift Journal", lifespan=lifespan)
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')


@app.get('/')
async def home():
    return FileResponse(ROOT / 'static/index.html')


@app.get('/champions/{champion_id}')
async def champion_page(champion_id: int):
    return FileResponse(ROOT / 'static/champion.html')


@app.get('/champions')
async def champions_page():
    return FileResponse(ROOT / 'static/champions.html')


@app.get('/tier-list')
async def tier_list_page():
    return FileResponse(ROOT / 'static/tier-list.html')


@app.get('/trends')
async def trends_page():
    return FileResponse(ROOT / 'static/trends.html')


@app.get('/api/trends')
async def get_trends(queue: Literal['all', 'solo', 'flex'] = 'all', role: Literal['all', 'TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'] = 'all', champion: int = Query(default=0, ge=0)):
    data = await get_dashboard(queue)
    if isinstance(data, JSONResponse):
        return data
    return performance_trends(data, time.time(), role, champion)


@app.get('/api/tier-list')
async def get_tier_list(queue: Literal['all', 'solo', 'flex'] = 'all', minimum: int = Query(default=3, ge=1, le=1000), period: Literal['all', '30d'] = 'all'):
    data = await get_dashboard(queue)
    if isinstance(data, JSONResponse):
        return data
    if period == '30d':
        cutoff = int((time.time() - 30 * 86400) * 1000)
        data = {**data, 'matches': [m for m in data['matches'] if cutoff <= m.get('playedAt', 0) <= int(time.time() * 1000)]}
    return {**champion_tiers(data, minimum), 'period': period}


async def fetch(client, url, key=None):
    global next_request
    if key:
        async with request_lock:
            await asyncio.sleep(max(0, next_request - time.monotonic()))
            next_request = time.monotonic() + 1.3
            return await fetch_response(client, url, key)
    return await fetch_response(client, url)


async def fetch_response(client, url, key=None):
    global next_request
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
        try:
            next_request = max(next_request, time.monotonic() + max(1, float(retry)))
        except ValueError:
            next_request = max(next_request, time.monotonic() + 120)
        raise RiotError(f'Riot rate limit reached. Try again in {retry} seconds.', 429)
    if not response.is_success:
        raise RiotError('Riot is temporarily unavailable. Please try again later.')
    try:
        return response.json()
    except ValueError:
        raise RiotError('Riot returned an unexpected response. Please try again.') from None


def match_summary(match, puuid):
    info = match['info']
    if not eligible_info(info):
        return None
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
        'score': score_player(info, player)['value'],
        'scoreVersion': '2',
        'role': player.get('teamPosition') or 'UNKNOWN',
    }


QUEUES = {'all': None, 'solo': 420, 'flex': 440}


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
    matches, warning = storage.matches(riot_id, QUEUES[queue]), None
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
                'championId': champion_id,
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
            'champions': [{**champion_data(cid), 'title': c.get('title', ''), 'tags': c.get('tags', [])} for cid, c in champions.items()],
            'updatedAt': int(time.time())}


@app.get('/api/dashboard')
async def get_dashboard(queue: Literal['all', 'solo', 'flex'] = 'all'):
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
        saved_profile = storage.profile(riot_id)
        if saved_profile or (cached and cached[0] > time.monotonic() and cached[1:3] == (key, riot_id)):
            data = dict(saved_profile or cached[3])
            data['queue'] = queue
            catalog = {c['championId']: c for c in data['champions']}
            data['matches'] = [{**m, **{k: v for k, v in catalog.get(m['championId'], {}).items() if k in ('name', 'icon')}} for m in storage.matches(riot_id, QUEUES[queue])]
            return enrich_dashboard(data)
        try:
            data = await dashboard(app.state.client, key, riot_id, queue)
        except RiotError as exc:
            return JSONResponse({'message': exc.message}, status_code=exc.status)
        cache[cache_key] = (time.monotonic() + 120, key, riot_id, data)
        storage.profile(riot_id, data)
        return enrich_dashboard(data)


@app.get('/api/champions/{champion_id}')
async def get_champion(champion_id: int, queue: Literal['all', 'solo', 'flex'] = 'all'):
    data = await get_dashboard(queue)
    if isinstance(data, JSONResponse):
        return data
    champion = next((c for c in data['champions'] if c['championId'] == champion_id), None)
    if champion is None:
        return JSONResponse({'message': 'Champion not found.'}, status_code=404)
    mastery = next((m for m in data['mastery'] if m['championId'] == champion_id), None)
    matches = [m for m in data['matches'] if m['championId'] == champion_id]
    return {**champion, 'riotId': data['riotId'], 'queue': queue,
            'mastery': mastery or {'points': 0, 'level': 0},
            'matches': matches, 'scoreStats': score_average(matches), 'lanes': lane_averages(matches),
            'sampleSize': len(data['matches']), 'warning': data['warning'],
            'updatedAt': data['updatedAt']}


@app.get('/api/sync')
async def get_sync():
    _, player = configuration()
    saved = storage.matches(player)
    return {**storage.state(player), **sync_status, 'saved': len(saved),
            'details': len(saved) - len(storage.pending(player, max(1, len(saved)))),
            'oldest': saved[-1]['playedAt'] if saved else None}


@app.post('/api/sync/{action}')
async def control_sync(action: Literal['pause', 'resume', 'more']):
    _, player = configuration()
    state = storage.state(player)
    if action == 'more':
        state['target'] = max(state['target'], len(storage.matches(player))) + 100
    state['paused'] = action == 'pause'
    storage.save_state(player, state)
    return await get_sync()


@app.get('/matches/{match_id}')
async def match_page(match_id: str):
    return FileResponse(ROOT / 'static/match.html')


@app.get('/matches')
async def matches_page():
    return FileResponse(ROOT / 'static/matches.html')


@app.get('/api/matches/{match_id}')
async def get_match(match_id: str):
    key, player = configuration()
    # Only fetch games already associated with the configured player.
    if not any(m['id'] == match_id for m in storage.matches(player)):
        return JSONResponse({'message': 'Match not found in your saved history.'}, status_code=404)
    stored = storage.detail(player, match_id)
    try:
        if stored is None:
            if not key:
                raise RiotError('Add your API key to load advanced details for this game.', 503)
            name, tag = player.rsplit('#', 1)
            account = await fetch(app.state.client, f'https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{quote(name, safe="")}/{quote(tag, safe="")}', key)
            raw = await fetch(app.state.client, f'https://europe.api.riotgames.com/lol/match/v5/matches/{quote(match_id, safe="")}', key)
            summary = match_summary(raw, account['puuid'])
            if summary is None:
                raise RiotError('This player was not found in the match.', 404)
            storage.save_match(player, summary)
            stored = storage.detail(player, match_id, {'raw': raw, 'puuid': account['puuid']})
        return await build_match_details(stored)
    except RiotError as exc:
        return JSONResponse({'message': exc.message}, status_code=exc.status)


async def build_match_details(stored):
    raw, puuid = stored['raw'], stored['puuid']
    info = raw['info']
    patch = '.'.join(info.get('gameVersion', '').split('.')[:2])
    asset_key = ('assets', patch)
    warning = None
    if asset_key not in cache:
        try:
            versions = await fetch(app.state.client, 'https://ddragon.leagueoflegends.com/api/versions.json')
            version = next((v for v in versions if v.startswith(patch + '.')), versions[0]) if patch else versions[0]
            base = f'https://ddragon.leagueoflegends.com/cdn/{version}'
            items = await fetch(app.state.client, f'{base}/data/en_US/item.json')
            spells = await fetch(app.state.client, f'{base}/data/en_US/summoner.json')
            runes = await fetch(app.state.client, f'{base}/data/en_US/runesReforged.json')
            cache[asset_key] = (base, items['data'], {int(v['key']): v for v in spells['data'].values()},
                                {r['id']: r for tree in runes for slot in tree['slots'] for r in slot['runes']})
        except RiotError:
            warning = 'Some item, spell, or rune labels could not be loaded. Raw IDs remain available.'
    base, items, spells, runes = cache.get(asset_key, ('', {}, {}, {}))
    profile = storage.profile(configuration()[1]) or {}
    champions = {c['championId']: c for c in profile.get('champions', [])}
    def asset(value, catalog, kind):
        entry = catalog.get(str(value), catalog.get(value, {}))
        icon = entry.get('icon') if kind == 'rune' else (f'{base}/img/{kind}/{entry["image"]["full"]}' if entry and base else None)
        if kind == 'rune' and icon:
            icon = f'https://ddragon.leagueoflegends.com/cdn/img/{icon}'
        return {'id': value, 'name': entry.get('name', f'{kind.title()} {value}'), 'icon': icon}
    participants = []
    fields = ['kills', 'deaths', 'assists', 'champLevel', 'goldEarned', 'totalDamageDealtToChampions',
              'physicalDamageDealtToChampions', 'magicDamageDealtToChampions', 'trueDamageDealtToChampions',
              'totalDamageTaken', 'damageSelfMitigated', 'visionScore', 'wardsPlaced', 'wardsKilled',
              'detectorWardsPlaced', 'damageDealtToObjectives', 'damageDealtToTurrets', 'turretTakedowns',
              'totalHealsOnTeammates', 'totalDamageShieldedOnTeammates', 'timeCCingOthers', 'totalTimeSpentDead']
    for p in info['participants']:
        champion = champions.get(p['championId'], {})
        perks = p.get('perks', {})
        team_kills = sum(q.get('kills', 0) for q in info['participants'] if q['teamId'] == p['teamId'])
        participants.append({**{f: p.get(f) for f in fields}, 'championId': p['championId'],
            'name': champion.get('name', p['championName']), 'icon': champion.get('icon'),
            'riotId': '#'.join(filter(None, [p.get('riotIdGameName') or p.get('summonerName') or p['championName'], p.get('riotIdTagline')])),
            'you': p.get('puuid') == puuid, 'teamId': p['teamId'], 'win': p.get('win'),
            'role': p.get('teamPosition') or 'Unknown',
            'cs': p.get('totalMinionsKilled', 0) + p.get('neutralMinionsKilled', 0),
            'kp': round((p.get('kills', 0) + p.get('assists', 0)) / team_kills * 100, 1) if team_kills else 0,
            'items': [asset(p.get(f'item{i}', 0), items, 'item') if p.get(f'item{i}') else None for i in range(7)],
            'spells': [asset(p.get(f'summoner{i}Id', 0), spells, 'spell') for i in (1, 2)],
            'runes': [asset(s['perk'], runes, 'rune') for style in perks.get('styles', []) for s in style.get('selections', [])],
            'statShards': perks.get('statPerks', {}), 'score': score_player(info, p)})
    return {'id': raw['metadata']['matchId'], 'mode': info.get('gameMode'), 'queue': info.get('queueId'),
            'duration': info.get('gameDuration', 0), 'playedAt': info.get('gameStartTimestamp', 0),
            'patch': info.get('gameVersion'), 'participants': participants,
            'teams': info.get('teams', []), 'warning': warning}
