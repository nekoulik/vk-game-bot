"""
Конфигурация ежедневных квестов и достижений.
"""

# Ключи должны совпадать с именами в increment_daily_stat!
DAILY_QUESTS = {
    "work": {
        "name": "Трудолюбивый",
        "description": "Поработать 3 раза",
        "target": 3,
        "stat": "work",
        "reward_coins": 100,
        "reward_exp": 10,
    },
    "duels": {
        "name": "Дуэлянт",
        "description": "Выиграть 2 дуэли",
        "target": 2,
        "stat": "duels_won",
        "reward_coins": 150,
        "reward_exp": 15,
    },
    "boss": {
        "name": "Охотник на боссов",
        "description": "Нанести 500 урона боссу",
        "target": 500,
        "stat": "boss_damage",
        "reward_coins": 300,
        "reward_exp": 30,
    },
    "bonus": {
        "name": "Ежедневный бонус",
        "description": "Получить ежедневный бонус",
        "target": 1,
        "stat": "bonus",
        "reward_coins": 50,
        "reward_exp": 5,
    },
    "games": {
        "name": "Игроман",
        "description": "Сыграть 5 раз в мини-игры",
        "target": 5,
        "stat": "games_played",
        "reward_coins": 80,
        "reward_exp": 8,
    },
}

ACHIEVEMENTS = {
    "first_work": {
        "name": "Первая работа",
        "description": "Поработать первый раз",
        "stat": "work",
        "target": 1,
        "reward_coins": 50,
        "reward_exp": 5,
    },
    "first_duel": {
        "name": "Первая дуэль",
        "description": "Выиграть первую дуэль",
        "stat": "duels_won",
        "target": 1,
        "reward_coins": 100,
        "reward_exp": 10,
    },
    "rich_player": {
        "name": "Богач",
        "description": "Накопить 10000 монет",
        "stat": "balance",
        "target": 10000,
        "reward_coins": 500,
        "reward_exp": 50,
    },
    "boss_slayer": {
        "name": "Убийца боссов",
        "description": "Убить 5 боссов",
        "stat": "boss_kills",
        "target": 5,
        "reward_coins": 1000,
        "reward_exp": 100,
    },
    "level_10": {
        "name": "Опытный игрок",
        "description": "Достичь 10 уровня",
        "stat": "level",
        "target": 10,
        "reward_coins": 200,
        "reward_exp": 0,
    },
}