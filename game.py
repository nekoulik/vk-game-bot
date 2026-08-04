import os
import json
import random
import time
import datetime

from vk_api import VkApi
from vk_api.utils import get_random_id
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))

if not TOKEN or not GROUP_ID:
    raise SystemExit("Создай файл .env и укажи VK_TOKEN и VK_GROUP_ID")

DATA_FILE = os.path.join(BASE_DIR, "players.json")
WORK_COOLDOWN_SECONDS = 60
MIN_BET = 10

session = VkApi(token=TOKEN)
api = session.get_api()

# ==================== МАГАЗИН ====================
ITEMS = {
    1: {"name": "🧪 Зелье здоровья", "price": 100, "type": "consumable", "desc": "Восстанавливает 30 HP в дуэли", "effect": {"hp": 30}},
    2: {"name": "⚔️ Ржавый меч", "price": 500, "type": "weapon", "desc": "+10 к урону в дуэлях", "effect": {"damage": 10}},
    3: {"name": "️ Стальной меч", "price": 1500, "type": "weapon", "desc": "+25 к урону в дуэлях", "effect": {"damage": 25}},
    4: {"name": "🛡️ Деревянный щит", "price": 400, "type": "armor", "desc": "-10 от получаемого урона", "effect": {"defense": 10}},
    5: {"name": "🛡️ Железный щит", "price": 1200, "type": "armor", "desc": "-25 от получаемого урона", "effect": {"defense": 25}},
    6: {"name": "👑 Корона", "price": 5000, "type": "cosmetic", "desc": "Для красоты в профиле", "effect": {}},
    7: {"name": "💎 Алмазный меч", "price": 5000, "type": "weapon", "desc": "+50 к урону в дуэлях", "effect": {"damage": 50}},
    8: {"name": "🧪 Большое зелье", "price": 250, "type": "consumable", "desc": "Восстанавливает 70 HP в дуэли", "effect": {"hp": 70}},
}


def load_players():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


players = load_players()


def save_players():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=2)


def get_name(user_id):
    try:
        users = api.users.get(user_ids=user_id)
        if users:
            full_name = f"{users[0].get('first_name', '')} {users[0].get('last_name', '')}".strip()
            if full_name:
                return full_name
    except Exception:
        pass
    return f"ID{user_id}"


def get_player(user_id):
    key = str(user_id)
    if key not in players:
        players[key] = {
            "name": get_name(user_id),
            "balance": 100,
            "level": 1,
            "exp": 0,
            "last_work": 0,
            "last_bonus": "",
            "bonus_streak": 0,
            "inventory": [],  # Список ID предметов
            "equipped": {     # Экипировка
                "weapon": None,
                "armor": None,
                "cosmetic": None,
            },
        }
        save_players()
    return players[key]


def send(peer_id, text):
    api.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())


def add_exp(player, amount=1):
    player["exp"] += amount
    leveled_up = False
    while player["exp"] >= player["level"] * 10:
        player["exp"] -= player["level"] * 10
        player["level"] += 1
        leveled_up = True
    return leveled_up


HELP_TEXT = """🎮 Игровой бот

Команды:
старт — начать
помощь — список команд
баланс — показать баланс
работа — заработать монеты
ставка 50 — сделать ставку
дуэль — сразиться с ботом
бонус — ежедневный бонус
топ — рейтинг игроков
профиль — показать профиль
магазин — купить предметы
инвентарь — твои предметы
купить <id> — купить предмет
использовать <id> — использовать предмет"""


def show_shop(peer_id):
    lines = ["🛒 **Магазин предметов**\n"]
    for item_id, item in ITEMS.items():
        lines.append(f"{item_id}. {item['name']} — {item['price']} монет")
        lines.append(f"   {item['desc']}")
        lines.append("")
    lines.append("💡 Купи: `купить <id>` (например: `купить 1`)")
    send(peer_id, "\n".join(lines))


def buy_item(player, peer_id, item_id_str):
    try:
        item_id = int(item_id_str)
    except ValueError:
        send(peer_id, "❌ Укажи ID предмета числом (пример: `купить 1`)")
        return

    if item_id not in ITEMS:
        send(peer_id, f"❌ Предмета с ID {item_id} не существует. Смотри `магазин`")
        return

    item = ITEMS[item_id]
    if player["balance"] < item["price"]:
        send(peer_id, f"❌ Недостаточно монет! Нужно {item['price']}, у тебя {player['balance']}")
        return

    player["balance"] -= item["price"]
    if "inventory" not in player:
        player["inventory"] = []
    player["inventory"].append(item_id)
    save_players()

    send(peer_id, f"✅ Куплено: {item['name']} за {item['price']} монет!\nТеперь в твоём инвентаре (`инвентарь`)")


def show_inventory(player, peer_id):
    if "inventory" not in player or not player["inventory"]:
        send(peer_id, "🎒 Твой инвентарь пуст. Загляни в `магазин`!")
        return

    lines = ["🎒 **Твой инвентарь**\n"]
    inventory = player["inventory"]
    
    # Считаем количество каждого предмета
    from collections import Counter
    counts = Counter(inventory)
    
    for item_id, count in sorted(counts.items()):
        if item_id in ITEMS:
            item = ITEMS[item_id]
            equipped_mark = ""
            # Проверяем, экипировано ли
            if player.get("equipped"):
                for slot, equipped_id in player["equipped"].items():
                    if equipped_id == item_id:
                        equipped_mark = " ⚡(экипировано)"
                        break
            lines.append(f"{item_id}. {item['name']} x{count}{equipped_mark}")
    
    lines.append("\n💡 Используй: `использовать <id>` или `экипировать <id>`")
    send(peer_id, "\n".join(lines))


def use_item(player, peer_id, item_id_str):
    try:
        item_id = int(item_id_str)
    except ValueError:
        send(peer_id, "❌ Укажи ID предмета числом")
        return

    if "inventory" not in player or item_id not in player["inventory"]:
        send(peer_id, "❌ У тебя нет этого предмета!")
        return

    if item_id not in ITEMS:
        send(peer_id, "❌ Неизвестный предмет")
        return

    item = ITEMS[item_id]
    
    if item["type"] == "consumable":
        # Расходник — просто удаляем один экземпляр
        player["inventory"].remove(item_id)
        save_players()
        send(peer_id, f"✅ Использовано: {item['name']}\n{item['desc']}")
    elif item["type"] in ["weapon", "armor", "cosmetic"]:
        # Экипировка — экипируем
        if "equipped" not in player:
            player["equipped"] = {"weapon": None, "armor": None, "cosmetic": None}
        
        slot = item["type"]
        old_item = player["equipped"].get(slot)
        player["equipped"][slot] = item_id
        save_players()
        
        if old_item:
            send(peer_id, f"✅ Экипировано: {item['name']}\n(предыдущее {ITEMS[old_item]['name']} снято)")
        else:
            send(peer_id, f"✅ Экипировано: {item['name']}\n{item['desc']}")
    else:
        send(peer_id, "❌ Этот предмет нельзя использовать")


def show_top(peer_id):
    ranked = sorted(
        players.items(),
        key=lambda item: (item[1]["level"], item[1]["balance"]),
        reverse=True,
    )[:10]

    medals = ["🥇", "🥈", ""]
    lines = [" Топ игроков:", ""]
    for i, (_, p) in enumerate(ranked, start=1):
        place = medals[i - 1] if i <= 3 else f"{i}."
        lines.append(f"{place} {p['name']} — ур. {p['level']}, {p['balance']} монет")

    send(peer_id, "\n".join(lines))


def claim_daily_bonus(player, peer_id):
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    if player.get("last_bonus") == today:
        send(peer_id, "🎁 Бонус уже получен сегодня. Возвращайся завтра!")
        return

    if player.get("last_bonus") == yesterday:
        player["bonus_streak"] = player.get("bonus_streak", 0) + 1
    else:
        player["bonus_streak"] = 1

    player["last_bonus"] = today
    reward = 50 + min(player["bonus_streak"], 10) * 10
    player["balance"] += reward
    add_exp(player, 1)
    save_players()

    send(
        peer_id,
        f"🎁 Ежедневный бонус: +{reward} монет!\n🔥 Серия входов: {player['bonus_streak']} дн.",
    )


def get_player_damage(player):
    """Считаем урон игрока с учётом экипировки"""
    base_damage = random.randint(12, 25)
    if player.get("equipped"):
        weapon_id = player["equipped"].get("weapon")
        if weapon_id and weapon_id in ITEMS:
            base_damage += ITEMS[weapon_id]["effect"].get("damage", 0)
    return base_damage


def get_player_defense(player):
    """Считаем защиту игрока"""
    defense = 0
    if player.get("equipped"):
        armor_id = player["equipped"].get("armor")
        if armor_id and armor_id in ITEMS:
            defense += ITEMS[armor_id]["effect"].get("defense", 0)
    return defense


def play_duel(player, peer_id):
    player_hp = 100
    bot_hp = 100
    log = []

    for round_number in range(1, 6):
        player_damage = get_player_damage(player)
        bot_damage = max(0, random.randint(12, 25) - get_player_defense(player))
        
        bot_hp -= player_damage
        player_hp -= bot_damage
        
        log.append(f"Раунд {round_number}: ты {player_damage}, бот {bot_damage}")
        if bot_hp <= 0 or player_hp <= 0:
            break

    if bot_hp <= 0 and player_hp > 0:
        reward = random.randint(30, 70)
        player["balance"] += reward
        add_exp(player, 3)
        save_players()
        result = f"🏆 Победа! Награда: {reward} монет."
    elif player_hp <= 0 and bot_hp > 0:
        add_exp(player, 1)
        save_players()
        result = "💀 Поражение. Попробуй ещё раз."
    else:
        add_exp(player, 1)
        save_players()
        result = "🤝 Ничья."

    send(peer_id, "️ Дуэль с ботом:\n" + "\n".join(log[-3:]) + "\n\n" + result)


def handle(user_id, peer_id, text):
    player = get_player(user_id)
    command = text.lower().strip()

    if not command:
        return

    if command in ["старт", "start", "/start", "!start", "помощь", "help"]:
        send(peer_id, f"{player['name']}, добро пожаловать!\n{HELP_TEXT}")
        return

    if command in ["баланс", "balance", "!баланс"]:
        send(peer_id, f"💰 Баланс: {player['balance']} монет.")
        return

    if command in ["работа", "work", "!работа"]:
        now = int(time.time())
        wait_seconds = WORK_COOLDOWN_SECONDS - (now - player.get("last_work", 0))
        if wait_seconds > 0:
            send(peer_id, f"⏳ Отдохни ещё {wait_seconds} сек.")
            return
        earned = random.randint(20, 80)
        player["balance"] += earned
        player["last_work"] = now
        level_up = add_exp(player, 2)
        save_players()
        message = f"👷 {player['name']}, ты заработал(а) {earned} монет."
        if level_up:
            message += f"\n🎉 Новый уровень: {player['level']}!"
        send(peer_id, message)
        return

    if command.startswith("ставка "):
        parts = command.split()
        if len(parts) != 2:
            send(peer_id, "Формат: ставка 50")
            return
        try:
            amount = int(parts[1])
        except ValueError:
            send(peer_id, "Ставка должна быть числом.")
            return
        if amount < MIN_BET:
            send(peer_id, f"Минимальная ставка: {MIN_BET} монет.")
            return
        if amount > player["balance"]:
            send(peer_id, "Недостаточно монет.")
            return
        player["balance"] -= amount
        if random.random() < 0.45:
            prize = amount * 2
            player["balance"] += prize
            message = f"🎰 Выигрыш! Ты получаешь {prize} монет."
        else:
            message = f"🎰 Не повезло. Ты потерял(а) {amount} монет."
        add_exp(player, 1)
        save_players()
        send(peer_id, message)
        return

    if command in ["дуэль", "duel", "!дуэль"]:
        play_duel(player, peer_id)
        return

    if command in ["бонус", "bonus", "!бонус", "ежедневный бонус"]:
        claim_daily_bonus(player, peer_id)
        return

    if command in ["топ", "top", "!топ", "рейтинг", "rating"]:
        show_top(peer_id)
        return

    if command in ["профиль", "profile", "!профиль"]:
        send(
            peer_id,
            "🧿 Профиль\n\n"
            f"Имя: {player['name']}\n"
            f"Уровень: {player['level']}\n"
            f"Опыт: {player['exp']}\n"
            f"Баланс: {player['balance']} монет\n"
            f"🔥 Серия бонусов: {player.get('bonus_streak', 0)} дн.",
        )
        return

    if command in ["магазин", "shop", "!магазин"]:
        show_shop(peer_id)
        return

    if command in ["инвентарь", "inv", "!инвентарь", "inventory"]:
        show_inventory(player, peer_id)
        return

    if command.startswith("купить "):
        parts = command.split()
        if len(parts) != 2:
            send(peer_id, "Формат: купить 1")
            return
        buy_item(player, peer_id, parts[1])
        return

    if command.startswith("использовать ") or command.startswith("use "):
        parts = command.split()
        if len(parts) != 2:
            send(peer_id, "Формат: использовать 1")
            return
        use_item(player, peer_id, parts[1])
        return

    if command.startswith("экипировать ") or command.startswith("equip "):
        parts = command.split()
        if len(parts) != 2:
            send(peer_id, "Формат: экипировать 2")
            return
        use_item(player, peer_id, parts[1])
        return

    send(peer_id, "Не понял команду. Напиши: помощь")