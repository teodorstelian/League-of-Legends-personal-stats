"""Provisional scoring styles derived from Riot tags and explicit app overrides."""
SPLIT_PUSHERS = {'Yorick', 'Tryndamere', 'Fiora', 'Jax', 'Nasus', 'Trundle', 'Sion', 'Illaoi'}


def archetype_for(player, tags=None):
    tags = tags or []
    primary = tags[0] if tags else None
    role = player.get('teamPosition')
    if role == 'UTILITY':
        if primary == 'Tank':
            return 'Tank support', 'tank'
        if primary in ('Mage', 'Marksman', 'Assassin'):
            return 'Damage support', 'damage_support'
        if tags:
            return 'Utility support', 'utility_support'
        return 'Support baseline (tags unavailable)', 'baseline'
    if role in ('TOP', 'MIDDLE') and player.get('championName') in SPLIT_PUSHERS:
        return 'Split-pusher', 'split'
    if primary == 'Support':
        primary = next((tag for tag in tags[1:] if tag in ('Tank','Fighter','Mage','Marksman','Assassin')), primary)
    if primary == 'Tank':
        return 'Tank', 'tank'
    if primary == 'Fighter':
        return 'Fighter', 'fighter'
    if primary in ('Mage', 'Marksman', 'Assassin'):
        return f'{primary} carry', 'carry'
    return ('Role baseline (unmapped tags)' if tags else 'Role baseline (tags unavailable)'), 'baseline'
