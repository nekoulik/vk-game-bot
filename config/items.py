"""Конфигурация предметов."""

ITEMS = {
    1: {"name": "Зелье здоровья", "price": 100, "type": "consumable", "desc": "Восстанавливает 30 HP в дуэли", "effect": {"hp": 30}},
    2: {"name": "Ржавый меч", "price": 500, "type": "weapon", "desc": "+10 к урону в дуэлях", "effect": {"damage": 10}},
    3: {"name": "Стальной меч", "price": 1500, "type": "weapon", "desc": "+25 к урону в дуэлях", "effect": {"damage": 25}},
    4: {"name": "Деревянный щит", "price": 400, "type": "armor", "desc": "-10 от получаемого урона", "effect": {"defense": 10}},
    5: {"name": "Железный щит", "price": 1200, "type": "armor", "desc": "-25 от получаемого урона", "effect": {"defense": 25}},
    6: {"name": "Корона", "price": 5000, "type": "cosmetic", "desc": "Для красоты в профиле", "effect": {}},
    7: {"name": "Алмазный меч", "price": 5000, "type": "weapon", "desc": "+50 к урону в дуэлях", "effect": {"damage": 50}},
    8: {"name": "Большое зелье", "price": 250, "type": "consumable", "desc": "Восстанавливает 70 HP в дуэли", "effect": {"hp": 70}},
}

ITEM_EMOJI = {1: "🧪", 2: "⚔️", 3: "️", 4: "🛡️", 5: "🛡️", 6: "👑", 7: "💎", 8: "🧪"}