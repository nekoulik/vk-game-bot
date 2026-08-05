"""Конфигурация боссов."""

BOSS_LEVELS = {
    1: {"name": "Гоблин-воин", "hp": 200, "attack": 15, "defense": 5, "reward": 100, "exp": 10},
    2: {"name": "Огр-разбойник", "hp": 400, "attack": 25, "defense": 10, "reward": 200, "exp": 20},
    3: {"name": "Тёмный рыцарь", "hp": 800, "attack": 35, "defense": 15, "reward": 400, "exp": 40},
    4: {"name": "Дракон", "hp": 1500, "attack": 50, "defense": 20, "reward": 800, "exp": 80},
    5: {"name": "Древний демон", "hp": 3000, "attack": 70, "defense": 30, "reward": 1500, "exp": 150},
}

BOSS_TIMEOUT_SECONDS = 600