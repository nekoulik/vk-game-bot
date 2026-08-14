"""
Пакет config — конфигурация бота.
"""
from config.settings import *
from config.shop import SHOP_ITEMS, WEAPONS, PETS

try:
    from config.clans import CLAN_BONUSES, SEASON_REWARDS
except ImportError:
    CLAN_BONUSES = {}
    SEASON_REWARDS = {}

try:
    from config.quests import DAILY_QUESTS, ACHIEVEMENTS
except ImportError:
    DAILY_QUESTS = {}
    ACHIEVEMENTS = {}
