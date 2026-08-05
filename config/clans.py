"""Конфигурация кланов."""

CLAN_BONUSES = {
    1: {"coins": 0.05, "exp": 0, "damage": 0},
    2: {"coins": 0.10, "exp": 0.05, "damage": 0},
    3: {"coins": 0.15, "exp": 0.10, "damage": 0.05},
    4: {"coins": 0.20, "exp": 0.15, "damage": 0.10},
    5: {"coins": 0.25, "exp": 0.20, "damage": 0.15},
}

SEASON_REWARDS = {
    1: {"coins": 1000, "title": "Чемпион"},
    2: {"coins": 500, "title": "Вице-чемпион"},
    3: {"coins": 250, "title": "Бронзовый"},
}