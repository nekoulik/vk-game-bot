"""
Клавиатуры для бота.
"""
import json


def get_main_keyboard():
    """Основное меню бота."""
    keyboard = {
        "one_time": False,
        "inline": False,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "label": "💰 Баланс",
                        "payload": json.dumps({"command": "баланс"})
                    },
                    "color": "positive"
                },
                {
                    "action": {
                        "type": "text",
                        "label": "👤 Профиль",
                        "payload": json.dumps({"command": "профиль"})
                    },
                    "color": "primary"
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "label": "💼 Работа",
                        "payload": json.dumps({"command": "работа"})
                    },
                    "color": "positive"
                },
                {
                    "action": {
                        "type": "text",
                        "label": "🎁 Бонус",
                        "payload": json.dumps({"command": "бонус"})
                    },
                    "color": "positive"
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "label": "🥇 Топ игроков",
                        "payload": json.dumps({"command": "топ"})
                    },
                    "color": "primary"
                },
                {
                    "action": {
                        "type": "text",
                        "label": "⚔️ Дуэль",
                        "payload": json.dumps({"command": "дуэль"})
                    },
                    "color": "negative"
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "label": "🛒 Магазин",
                        "payload": json.dumps({"command": "магазин"})
                    },
                    "color": "secondary"
                },
                {
                    "action": {
                        "type": "text",
                        "label": "🎮 Игры",
                        "payload": json.dumps({"command": "игры"})
                    },
                    "color": "secondary"
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "label": "💀 Босс",
                        "payload": json.dumps({"command": "босс"})
                    },
                    "color": "negative"
                },
                {
                    "action": {
                        "type": "text",
                        "label": "📋 Квесты",
                        "payload": json.dumps({"command": "квесты"})
                    },
                    "color": "primary"
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "label": "⚔️ PvP",
                        "payload": json.dumps({"command": "pvp"})
                    },
                    "color": "negative"
                },
                {
                    "action": {
                        "type": "text",
                        "label": "️🛡️ Клан",
                        "payload": json.dumps({"command": "клан"})
                    },
                    "color": "primary"
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "label": "🌟 Сезон",
                        "payload": json.dumps({"command": "сезон"})
                    },
                    "color": "primary"
                },
                {
                    "action": {
                        "type": "text",
                        "label": "ℹ️ Помощь",
                        "payload": json.dumps({"command": "помощь"})
                    },
                    "color": "secondary"
                }
            ]
        ]
    }
    return keyboard


def get_admin_keyboard():
    """Админ-панель."""
    keyboard = {
        "one_time": False,
        "inline": False,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "label": "📊 Статистика",
                        "payload": json.dumps({"command": "статистика"})
                    },
                    "color": "primary"
                },
                {
                    "action": {
                        "type": "text",
                        "label": "👥 Игроки",
                        "payload": json.dumps({"command": "игроки"})
                    },
                    "color": "primary"
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "label": "⚙️ Настройки беседы",
                        "payload": json.dumps({"command": "настройки беседы"})
                    },
                    "color": "secondary"
                }
            ],
            [
                {
                    "action": {
                        "type": "text",
                        "label": "🔙 В главное меню",
                        "payload": json.dumps({"command": "помощь"})
                    },
                    "color": "negative"
                }
            ]
        ]
    }
    return keyboard