"""Конфигурация магазина."""

# Зелья
POTIONS = {
    1: {"name": "Зелье здоровья", "price": 100, "item_id": "health_potion", "emoji": "💚", "category": "potions"},
    2: {"name": "Зелье силы", "price": 150, "item_id": "strength_potion", "emoji": "🛡️", "category": "potions"},
    3: {"name": "Зелье скорости", "price": 200, "item_id": "speed_potion", "emoji": "⚡", "category": "potions"},
}

# Оружие
WEAPONS = {
    4: {"name": "Деревянный меч", "price": 500, "item_id": "wooden_sword", "emoji": "🗡️", "category": "weapons", "damage": 5},
    5: {"name": "Стальной меч", "price": 1500, "item_id": "steel_sword", "emoji": "⚔️", "category": "weapons", "damage": 15},
    6: {"name": "Огненный топор", "price": 3000, "item_id": "fire_axe", "emoji": "🪓", "category": "weapons", "damage": 30},
    7: {"name": "Магический посох", "price": 5000, "item_id": "magic_staff", "emoji": "🔮", "category": "weapons", "damage": 50},
    8: {"name": "Легендарный клинок", "price": 10000, "item_id": "legendary_blade", "emoji": "✨", "category": "weapons", "damage": 100},
}

# Питомцы
PETS = {
    9: {"name": "Кот", "price": 1000, "item_id": "pet_cat", "emoji": "🐱", "category": "pets", "bonus": "+5% к монетам"},
    10: {"name": "Собака", "price": 2000, "item_id": "pet_dog", "emoji": "", "category": "pets", "bonus": "+10% к урону"},
    11: {"name": "Дракон", "price": 5000, "item_id": "pet_dragon", "emoji": "", "category": "pets", "bonus": "+20% к монетам"},
    12: {"name": "Феникс", "price": 10000, "item_id": "pet_phoenix", "emoji": "🦅", "category": "pets", "bonus": "+30% к урону"},
    13: {"name": "Единорог", "price": 15000, "item_id": "pet_unicorn", "emoji": "🦄", "category": "pets", "bonus": "+50% ко всему"},
}

# Объединённый магазин
SHOP_ITEMS = {**POTIONS, **WEAPONS, **PETS}