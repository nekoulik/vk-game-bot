import os
from dotenv import load_dotenv

load_dotenv()

VK_TOKEN = os.getenv('VK_TOKEN')
VK_GROUP_ID = int(os.getenv('VK_GROUP_ID', '0'))

# Админы - список ID через запятую
ADMIN_IDS_RAW = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(',') if x.strip()]

DATABASE_PATH = 'game.db'

# Настройки бота
BOT_NAME = 'Club Anicoke'
BOT_VERSION = '1.0.0'

# Экономика
DAILY_BONUS = 100
WORK_REWARD_MIN = 50
WORK_REWARD_MAX = 150

# Босс
BOSS_MAX_HP = 10000
BOSS_REWARD = 500