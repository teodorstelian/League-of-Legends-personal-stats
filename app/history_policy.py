RANKED_QUEUES = (420, 440)
MIN_DURATION = 180


def eligible_summary(match):
    return match.get('queue') in RANKED_QUEUES and match.get('duration', 0) >= MIN_DURATION and not match.get('remake', False)


def eligible_info(info):
    return (info.get('queueId') in RANKED_QUEUES and info.get('gameDuration', 0) >= MIN_DURATION
            and not any(p.get('gameEndedInEarlySurrender') for p in info.get('participants', [])))
