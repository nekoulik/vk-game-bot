# 🎮 VK Game Bot - Club Anicoke

**Многофункциональный игровой бот для ВКонтакте с экономикой, PvP-дуэлями и мини-играми**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![VK API](https://img.shields.io/badge/VK%20API-11.9-green.svg)](https://vk.com/dev/bots_docs)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Описание

**Club Anicoke** — это современный игровой бот для ВКонтакте, который предоставляет пользователям широкий спектр развлечений: от экономической системы и PvP-дуэлей до мини-игр и клановых сражений.

### ✨ Основные возможности:

- 💰 **Экономическая система** — зарабатывай монеты, работай, получай бонусы
- ️ **PvP-дуэли** — сражайся с другими игроками или с ботом
- 👹 **Босс-файты** — объединяйся с другими для победы над боссом
- 🎲 **Мини-игры** — камень-ножницы-бумага, угадай число, лотерея
-  **Питомцы** — покупай и активируй питомцев для получения бонусов
- 🏆 **Система прогресса** — квесты, достижения, сезонные награды
- 🏰 **Кланы** — создавай кланы, сражайся в клановых войнах
- 🔔 **Уведомления** — настраивай уведомления о событиях

---

## 🚀 Быстрый старт

### Требования

- Python 3.8+
- Аккаунт ВКонтакте и созданное сообщество
- Токен группы с правами на сообщения

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/nekoulik/vk-game-bot.git
cd vk-game-bot

2.Установите зависимости: pip install -r requirements.txt
3.Настройте переменные окружения: cp .env.example .env
4.Откройте .env и укажите: VK_TOKEN=your_bot_token_here VK_GROUP_ID=your_group_id_here
5.Запустите бота: python main.py

📂 Структура проекта

vk-game-bot/
├── main.py                 # Точка входа, обработка Long Poll
├── server.py               # WSGI-приложение для сайта
├── requirements.txt        # Зависимости Python
├── .env                    # Переменные окружения
├── game.db                 # SQLite база данных
├── commands/               # Обработчики команд (basic, shop, pets, boss, quests, seasons, games, clans, notifications, admin)
├── db/                     # Работа с базой данных (players, items, pets, boss, duels, quests, seasons, clans, notifications)
├── config/                 # Конфигурация (settings.py)
└── utils/                  # Вспомогательные функции (helpers.py)

🎮 Команды бота

Основные: /старт, /помощь, /баланс, /работа, /бонус, /топ, /профиль
Экономика: /магазин, /инвентарь, /купить <id>, /экипировать <id>
PvP и дуэли: /вызов @id123, /принять, /отклонить, /дуэль, /ставка <сумма>
Босс: /босс, /атака, /статус, /сдаться
Игры: /кнб <камень|ножницы|бумага>, /угадай <число>, /лотерея
Питомцы: /питомцы, /купить питомца <id>, /мои питомцы, /активировать <id>
Прогресс: /квесты, /выполнить квесты, /достижения, /сезон, /история сезонов
Кланы: /клан, /клан создать <название>, /кланы, /клан вступить <ID>
Настройки: /настройки, /включить <тип>, /выключить <тип>

🛠️ Технологии

Python 3.8+ — язык программирования
vk_api — работа с VK API
SQLite — база данных
python-dotenv — управление переменными окружения
WSGI — веб-сервер для PythonAnywhere

🌐 Развёртывание на PythonAnywhere

1.Создайте аккаунт на PythonAnywhere
2.Загрузите код через Git: git clone https://github.com/nekoulik/vk-game-bot.git
3.Установите зависимости: pip install -r requirements.txt --user
4.Настройте .env файл с вашим токеном
5.Создайте базу данных: python3 -c "import db; db.init_db(); print('✅ БД создана')"
6.Настройте WSGI (вкладка Web → WSGI configuration file):

import sys
path = '/home/yourusername/vk-game-bot'
if path not in sys.path:
sys.path.insert(0, path)
from server import application

7.Запустите бота в Bash-консоли: cd ~/vk-game-bot && python3 main.py > bot.log 2>&1 &

🔧 Настройка (.env)

VK_TOKEN=your_token_here
VK_GROUP_ID=123456789
ADMIN_IDS=123456789,987654321

📊 Статистика

14 таблиц в базе данных
50+ команд для пользователей
10+ мини-игр и активностей
Автоматические уведомления о событиях
Защита от дубликатов сообщений

🤝 Вклад

1.Contributions welcome!
2.Fork репозиторий
3.Создайте ветку (git checkout -b feature/AmazingFeature)
4.Закоммитьте изменения (git commit -m 'Add some AmazingFeature')
5.Отправьте в ветку (git push origin feature/AmazingFeature)
6.Откройте Pull Request

📝 Лицензия

Распространяется под лицензией MIT.

👥 Контакты

ВКонтакте: Club Anicoke
GitHub: @nekoulik
Сайт: https://nekoulik.pythonanywhere.com

Made with ❤️ by Club Anicoke Team
