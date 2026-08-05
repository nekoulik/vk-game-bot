"""Конфигурация квестов и достижений."""

DAILY_QUESTS = {
    "duels": {"target": 3, "reward_coins": 100, "reward_exp": 10, "name": "Сыграть 3 дуэли"},
    "boss": {"target": 1, "reward_coins": 150, "reward_exp": 15, "name": "Участвовать в бою с боссом"},
    "coins": {"target": 200, "reward_coins": 50, "reward_exp": 5, "name": "Заработать 200 монет"},
}

ACHIEVEMENTS = {
    "first_blood": {"name": "Первая кровь", "desc": "Выиграть 1 дуэль"},
    "rich": {"name": "Богач", "desc": "Накопить 1000 монет"},
    "boss_slayer": {"name": "Истребитель", "desc": "Убить 3 боссов"},
}