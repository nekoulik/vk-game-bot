import os
import json
import random
import time
import datetime
from collections import Counter

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
DUELS_FILE = os.path.join(BASE_DIR, "duels.json")
BOSS_FILE = os.path.join(BASE_DIR, "boss.json")
WORK_COOLDOWN_SECONDS = 60
MIN_BET = 10
DUEL_TIMEOUT_SECONDS = 300
BOSS_TIMEOUT_SECONDS = 300  # 5 минут на бой с боссом

session = VkApi(token=TOKEN)
api = session.get_api()

# ==================== МАГАЗИН ====================
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

ITEM_EMOJI = {
    1: "🧪", 2: "⚔️", 3: "️", 4: "🛡️", 5: "🛡️",
    6: "👑", 7: "💎", 8: "🧪",
}

# ==================== БОССЫ ====================
BOSS_LEVELS = {
    1: {"name": "Гоблин-воин", "hp": 200, "attack": 15, "defense": 5, "reward": 100, "exp": 10},
    2: {"name": "Огр-разбойник", "hp": 400, "attack": 25, "defense": 10, "reward": 200, "exp": 20},
    3: {"name": "Тёмный рыцарь", "hp": 800, "attack": 35, "defense": 15, "reward": 400, "exp": 40},
    4: {"name": "Дракон", "hp": 1500, "attack": 50, "defense": 20, "reward": 800, "exp": 80},
    5: {"name": "Древний демон", "hp": 3000, "attack": 70, "defense": 30, "reward": 1500, "exp": 150},
}


# ==================== ЗАГРУЗКА/СОХРАНЕНИЕ ====================
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


def load_duels():
    if os.path.exists(DUELS_FILE):
        try:
            with open(DUELS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_duels(duels):
    with open(DUELS_FILE, "w", encoding="utf-8") as f:
        json.dump(duels, f, ensure_ascii=False, indent=2)


def load_boss():
    if os.path.exists(BOSS_FILE):
        try:
            with open(BOSS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_boss(boss_data):
    with open(BOSS_FILE, "w", encoding="utf-8") as f:
        json.dump(boss_data, f, ensure_ascii=False, indent=2)


# ==================== ИГРОКИ ====================
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
            "inventory": [],
            "equipped": {
                "weapon": None,
                "armor": None,
                "cosmetic": None,
            },
            "last_peer_id": None,
        }
        save_players()
    return players[key]


# ==================== ОТПРАВКА ====================
def send(peer_id, text):
    try:
        api.messages.send(peer_id=peer_id, message=text, random_id=get_random_id())
    except Exception as e:
        print(f"Ошибка отправки в {peer_id}: {e}")


# ==================== ОПЫТ ====================
def add_exp(player, amount=1):
    player["exp"] += amount
    leveled_up = False
    while player["exp"] >= player["level"] * 10:
        player["exp"] -= player["level"] * 10
        player["level"] += 1
        leveled_up = True
    return leveled_up


# ==================== СПРАВКА ====================
HELP_TEXT = (
    "Игровой бот\n\n"
    "Основные:\n"
    "старт — начать\n"
    "помощь — список команд\n"
    "баланс — показать баланс\n"
    "работа — заработать монеты\n"
    "ставка 50 — сделать ставку\n"
    "дуэль — сразиться с ботом\n"
    "бонус — ежедневный бонус\n"
    "топ — рейтинг игроков\n"
    "профиль — показать профиль\n\n"
    "Магазин:\n"
    "магазин — каталог предметов\n"
    "инвентарь — твои предметы\n"
    "купить <id> — купить предмет\n"
    "экипировать <id> — надеть предмет\n\n"
    "PvP:\n"
    "вызов @id123 — вызвать игрока на дуэль\n"
    "принять — принять вызов\n"
    "отклонить — отклонить вызов\n\n"
    "Босс:\n"
    "босс — начать/присоединиться к бою\n"
    "атака — атаковать босса\n"
    "статус — показать HP босса\n"
    "сдаться — покинуть бой"
)


# ==================== МАГАЗИН ====================
def show_shop(peer_id):
    lines = ["Магазин предметов\n"]
    for item_id, item in ITEMS.items():
        emoji = ITEM_EMOJI.get(item_id, "📦")
        lines.append(f"{item_id}. {emoji} {item['name']} — {item['price']} монет")
        lines.append(f"   {item['desc']}")
        lines.append("")
    lines.append("Чтобы купить, напиши: купить <номер> (например: купить 1)")
    send(peer_id, "\n".join(lines))


def buy_item(player, peer_id, item_id_str):
    try:
        item_id = int(item_id_str)
    except ValueError:
        send(peer_id, "Укажи номер предмета числом (пример: купить 1)")
        return

    if item_id not in ITEMS:
        send(peer_id, f"Предмета с номером {item_id} нет. Смотри: магазин")
        return

    item = ITEMS[item_id]
    if player["balance"] < item["price"]:
        send(peer_id, f"Недостаточно монет! Нужно {item['price']}, у тебя {player['balance']}")
        return

    player["balance"] -= item["price"]
    if "inventory" not in player:
        player["inventory"] = []
    player["inventory"].append(item_id)
    save_players()

    emoji = ITEM_EMOJI.get(item_id, "📦")
    send(peer_id, f"Куплено: {emoji} {item['name']} за {item['price']} монет!\nТеперь в твоём инвентаре (команда: инвентарь)")


def show_inventory(player, peer_id):
    if "inventory" not in player or not player["inventory"]:
        send(peer_id, "Твой инвентарь пуст. Загляни в магазин!")
        return

    lines = ["Твой инвентарь\n"]
    inventory = player["inventory"]
    counts = Counter(inventory)

    for item_id, count in sorted(counts.items()):
        if item_id in ITEMS:
            item = ITEMS[item_id]
            emoji = ITEM_EMOJI.get(item_id, "")
            equipped_mark = ""
            if player.get("equipped"):
                for slot, equipped_id in player["equipped"].items():
                    if equipped_id == item_id:
                        equipped_mark = " (надето)"
                        break
            lines.append(f"{item_id}. {emoji} {item['name']} x{count}{equipped_mark}")

    lines.append("\nНадеть: экипировать <номер>")
    send(peer_id, "\n".join(lines))


def use_item(player, peer_id, item_id_str):
    try:
        item_id = int(item_id_str)
    except ValueError:
        send(peer_id, "Укажи номер предмета числом")
        return

    if "inventory" not in player or item_id not in player["inventory"]:
        send(peer_id, "У тебя нет этого предмета!")
        return

    if item_id not in ITEMS:
        send(peer_id, "Неизвестный предмет")
        return

    item = ITEMS[item_id]
    emoji = ITEM_EMOJI.get(item_id, "")

    if item["type"] == "consumable":
        player["inventory"].remove(item_id)
        save_players()
        send(peer_id, f"Использовано: {emoji} {item['name']}\n{item['desc']}")
    elif item["type"] in ["weapon", "armor", "cosmetic"]:
        if "equipped" not in player:
            player["equipped"] = {"weapon": None, "armor": None, "cosmetic": None}

        slot = item["type"]
        old_item = player["equipped"].get(slot)
        player["equipped"][slot] = item_id
        save_players()

        if old_item and old_item in ITEMS:
            send(peer_id, f"Надето: {emoji} {item['name']}\n(предыдущее {ITEMS[old_item]['name']} снято)")
        else:
            send(peer_id, f"Надето: {emoji} {item['name']}\n{item['desc']}")
    else:
        send(peer_id, "Этот предмет нельзя использовать")


# ==================== ТОП ====================
def show_top(peer_id):
    ranked = sorted(
        players.items(),
        key=lambda item: (item[1]["level"], item[1]["balance"]),
        reverse=True,
    )[:10]

    medals = ["1 место", "2 место", "3 место"]
    lines = ["Топ игроков:\n"]
    for i, (_, p) in enumerate(ranked, start=1):
        place = medals[i - 1] if i <= 3 else f"{i}."
        lines.append(f"{place} {p['name']} — ур. {p['level']}, {p['balance']} монет")

    send(peer_id, "\n".join(lines))


# ==================== ЕЖЕДНЕВНЫЙ БОНУС ====================
def claim_daily_bonus(player, peer_id):
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    if player.get("last_bonus") == today:
        send(peer_id, "Бонус уже получен сегодня. Возвращайся завтра!")
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
        f"Ежедневный бонус: +{reward} монет!\nСерия входов: {player['bonus_streak']} дн.",
    )


# ==================== ДУЭЛЬ С БОТОМ ====================
def get_player_damage(player):
    base_damage = random.randint(12, 25)
    if player.get("equipped"):
        weapon_id = player["equipped"].get("weapon")
        if weapon_id and weapon_id in ITEMS:
            base_damage += ITEMS[weapon_id]["effect"].get("damage", 0)
    return base_damage


def get_player_defense(player):
    defense = 0
    if player.get("equipped"):
        armor_id = player["equipped"].get("armor")
        if armor_id and armor_id in ITEMS:
            defense += ITEMS[armor_id]["effect"].get("defense", 0)
    return defense


def play_duel_vs_bot(player, peer_id):
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
        result = f"Победа! Награда: {reward} монет."
    elif player_hp <= 0 and bot_hp > 0:
        add_exp(player, 1)
        save_players()
        result = "Поражение. Попробуй ещё раз."
    else:
        add_exp(player, 1)
        save_players()
        result = "Ничья."

    send(peer_id, "Дуэль с ботом:\n" + "\n".join(log[-3:]) + "\n\n" + result)


# ==================== PvP ДУЭЛИ ====================
def parse_user_id_from_mention(text):
    import re
    m = re.search(r'\[id(\d+)', text)
    if m:
        return int(m.group(1))
    m = re.search(r'@id(\d+)', text)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d{5,10})', text)
    if m:
        return int(m.group(1))
    return None


def challenge_player(challenger_id, challenged_id, challenger_peer_id):
    if challenged_id == challenger_id:
        send(challenger_peer_id, "Нельзя вызвать самого себя на дуэль!")
        return

    if str(challenged_id) not in players:
        send(challenger_peer_id, "Этот игрок ещё не начинал игру. Пусть сначала напишет боту 'старт'.")
        return

    duels = load_duels()

    if str(challenged_id) in duels:
        existing = duels[str(challenged_id)]
        if time.time() - existing.get("timestamp", 0) < DUEL_TIMEOUT_SECONDS:
            send(challenger_peer_id, "Этот игрок уже получил вызов. Подождите, пока он ответит.")
            return

    duels[str(challenged_id)] = {
        "challenger_id": challenger_id,
        "challenger_peer_id": challenger_peer_id,
        "timestamp": time.time(),
    }
    save_duels(duels)

    challenged_player = get_player(challenged_id)
    challenger_player = get_player(challenger_id)

    send(challenger_peer_id, f"Вы вызвали {challenged_player['name']} на дуэль! Ждём ответа...")
    
    challenged_peer_id = challenged_player.get("last_peer_id")
    if challenged_peer_id:
        send(challenged_peer_id,
             f"⚔️ {challenger_player['name']} вызывает вас на дуэль!\nНапишите: принять\nИли: отклонить")
    else:
        send(challenger_peer_id, "Но игрок ещё не писал боту — он не получит уведомление.")


def accept_duel(challenged_id, challenged_peer_id):
    duels = load_duels()

    if str(challenged_id) not in duels:
        send(challenged_peer_id, "У вас нет активных вызовов на дуэль.")
        return

    challenge = duels[str(challenged_id)]

    if time.time() - challenge.get("timestamp", 0) >= DUEL_TIMEOUT_SECONDS:
        del duels[str(challenged_id)]
        save_duels(duels)
        send(challenged_peer_id, "Вызов истёк. Попросите вызвать вас снова.")
        return

    challenger_id = challenge["challenger_id"]
    challenger_peer_id = challenge["challenger_peer_id"]

    del duels[str(challenged_id)]
    save_duels(duels)

    send(challenged_peer_id, "Вы приняли вызов! Начинается дуэль...")
    send(challenger_peer_id, "Соперник принял вызов! Начинается дуэль...")

    player1 = get_player(challenger_id)
    player2 = get_player(challenged_id)

    play_pvp_duel(player1, player2, challenger_peer_id, challenged_peer_id)


def decline_duel(challenged_id, challenged_peer_id):
    duels = load_duels()

    if str(challenged_id) not in duels:
        send(challenged_peer_id, "У вас нет активных вызовов на дуэль.")
        return

    challenge = duels[str(challenged_id)]
    challenger_id = challenge["challenger_id"]
    challenger_peer_id = challenge["challenger_peer_id"]

    del duels[str(challenged_id)]
    save_duels(duels)

    challenger_player = get_player(challenger_id)
    send(challenged_peer_id, "Вы отклонили вызов на дуэль.")
    send(challenger_peer_id, f"{challenger_player['name']} отклонил ваш вызов на дуэль.")


def play_pvp_duel(player1, player2, peer1_id, peer2_id):
    hp1 = 100
    hp2 = 100
    log = []

    for round_number in range(1, 8):
        if hp1 <= 0 or hp2 <= 0:
            break

        dmg1 = get_player_damage(player1)
        dmg2 = get_player_damage(player2)
        def1 = get_player_defense(player1)
        def2 = get_player_defense(player2)

        actual_dmg1 = max(3, dmg1 - def2)
        actual_dmg2 = max(3, dmg2 - def1)

        hp2 -= actual_dmg1
        hp1 -= actual_dmg2

        log.append(f"Раунд {round_number}: {player1['name']} -{actual_dmg1}, {player2['name']} -{actual_dmg2}")

    if hp1 > 0 and hp2 <= 0:
        reward = random.randint(50, 100)
        player1["balance"] += reward
        add_exp(player1, 5)
        add_exp(player2, 2)
        save_players()
        result = f"🏆 Победил {player1['name']}! Награда: {reward} монет."
    elif hp2 > 0 and hp1 <= 0:
        reward = random.randint(50, 100)
        player2["balance"] += reward
        add_exp(player2, 5)
        add_exp(player1, 2)
        save_players()
        result = f"🏆 Победил {player2['name']}! Награда: {reward} монет."
    else:
        add_exp(player1, 2)
        add_exp(player2, 2)
        save_players()
        result = "Ничья. Оба получают опыт."

    duel_log = "\n".join(log[-5:])
    result_message = f"⚔️ PvP дуэль:\n{duel_log}\n\n{result}"

    send(peer1_id, result_message)
    if peer2_id != peer1_id:
        send(peer2_id, result_message)


# ==================== БОСС ====================
def start_boss_fight(user_id, peer_id):
    """Начать или присоединиться к бою с боссом"""
    boss_data = load_boss()

    # Проверяем, есть ли активный бой
    if boss_data.get("active"):
        # Проверяем таймаут
        if time.time() - boss_data.get("start_time", 0) > BOSS_TIMEOUT_SECONDS:
            # Таймаут истёк — сбрасываем
            boss_data = {}
            save_boss(boss_data)
            send(peer_id, "Предыдущий бой истёк. Начинаем нового босса!")
            return create_new_boss(user_id, peer_id)
        
        # Бой активен — присоединяемся
        if str(user_id) in boss_data.get("participants", {}):
            send(peer_id, "Ты уже участвуешь в бою! Пиши 'атака' чтобы бить.")
            return
        
        player = get_player(user_id)
        boss_data["participants"][str(user_id)] = {
            "name": player["name"],
            "damage": 0,
            "peer_id": peer_id,
        }
        save_boss(boss_data)
        
        boss_level = boss_data.get("level", 1)
        boss_name = BOSS_LEVELS[boss_level]["name"]
        send(peer_id, f"Ты присоединился к бою с {boss_name}!\nHP босса: {boss_data['current_hp']}/{boss_data['max_hp']}\nПиши 'атака' чтобы атаковать.")
        return

    # Начинаем новый бой
    create_new_boss(user_id, peer_id)


def create_new_boss(user_id, peer_id):
    """Создать нового босса"""
    player = get_player(user_id)
    
    # Определяем уровень босса на основе уровня игрока
    player_level = player.get("level", 1)
    if player_level <= 2:
        boss_level = 1
    elif player_level <= 5:
        boss_level = 2
    elif player_level <= 10:
        boss_level = 3
    elif player_level <= 15:
        boss_level = 4
    else:
        boss_level = 5
    
    boss = BOSS_LEVELS[boss_level]
    
    boss_data = {
        "active": True,
        "level": boss_level,
        "name": boss["name"],
        "max_hp": boss["hp"],
        "current_hp": boss["hp"],
        "attack": boss["attack"],
        "defense": boss["defense"],
        "start_time": time.time(),
        "participants": {
            str(user_id): {
                "name": player["name"],
                "damage": 0,
                "peer_id": peer_id,
            }
        },
    }
    
    save_boss(boss_data)
    
    send(peer_id, 
         f"👹 {boss['name']} (ур. {boss_level}) появился!\n"
         f"HP: {boss['hp']}\n"
         f"Атака: {boss['attack']}\n"
         f"Защита: {boss['defense']}\n\n"
         f"Пиши 'атака' чтобы бить!\n"
         f"Другие могут присоединиться командой 'босс'")


def attack_boss(user_id, peer_id):
    boss_data = load_boss()
    
    # === ОТЛАДКА ===
    print(f"[BOSS DEBUG] attack_boss called")
    print(f"[BOSS DEBUG] boss_data: {boss_data}")
    print(f"[BOSS DEBUG] current_time: {time.time()}")
    print(f"[BOSS DEBUG] start_time: {boss_data.get('start_time', 'NOT SET')}")
    if boss_data.get('start_time'):
        elapsed = time.time() - boss_data.get('start_time', 0)
        print(f"[BOSS DEBUG] elapsed time: {elapsed} seconds")
    # ===============

    if not boss_data.get("active"):
        send(peer_id, "Сейчас нет активного боя. Напиши 'босс' чтобы начать!")
        return

    # Проверяем таймаут
    if time.time() - boss_data.get("start_time", 0) > BOSS_TIMEOUT_SECONDS:
        boss_data = {}
        save_boss(boss_data)
        send(peer_id, "Бой истёк. Напиши 'босс' чтобы начать нового.")
        return

    # Проверяем, участник ли
    if str(user_id) not in boss_data["participants"]:
        send(peer_id, "Ты не участвуешь в этом бою! Напиши 'босс' чтобы присоединиться.")
        return

    player = get_player(user_id)
    boss_name = boss_data["name"]
    boss_defense = boss_data.get("defense", 0)
    
    # Считаем урон
    damage = get_player_damage(player)
    actual_damage = max(1, damage - boss_defense)
    
    # Наносим урон
    boss_data["current_hp"] -= actual_damage
    boss_data["participants"][str(user_id)]["damage"] += actual_damage
    
    # Босс атакует в ответ (случайный урон)
    boss_attack = boss_data.get("attack", 10)
    player_defense = get_player_defense(player)
    boss_damage = max(1, boss_attack - player_defense)
    
    # Сохраняем
    save_boss(boss_data)
    
    send(peer_id, f"Ты нанёс {actual_damage} урона {boss_name}!\n"
         f"HP босса: {max(0, boss_data['current_hp'])}/{boss_data['max_hp']}\n"
         f"Босс атакует тебя на {boss_damage} урона.")
    
    # Проверяем, не умер ли босс
    if boss_data["current_hp"] <= 0:
        defeat_boss(boss_data)


def defeat_boss(boss_data):
    """Босс побеждён — распределяем награды"""
    boss_level = boss_data["level"]
    base_reward = BOSS_LEVELS[boss_level]["reward"]
    base_exp = BOSS_LEVELS[boss_level]["exp"]
    
    total_damage = sum(p["damage"] for p in boss_data["participants"].values())
    
    messages = [f" {boss_data['name']} повержен!\n\nНаграды:\n"]
    
    for participant_id, data in boss_data["participants"].items():
        if total_damage > 0:
            share = data["damage"] / total_damage
        else:
            share = 1 / len(boss_data["participants"])
        
        reward = int(base_reward * share)
        exp = int(base_exp * share)
        
        player = get_player(int(participant_id))
        player["balance"] += reward
        add_exp(player, exp)
        
        messages.append(f"{data['name']}: +{reward} монет, +{exp} опыта\n"
                       f"   (нанёс {data['damage']} урона)")
    
    save_players()
    boss_data["active"] = False
    save_boss(boss_data)
    
    # Отправляем всем участникам
    for participant_id, data in boss_data["participants"].items():
        peer_id = data.get("peer_id", int(participant_id))
        send(peer_id, "\n".join(messages))


def show_boss_status(user_id, peer_id):
    """Показать статус боя с боссом"""
    boss_data = load_boss()

    if not boss_data.get("active"):
        send(peer_id, "Сейчас нет активного боя. Напиши 'босс' чтобы начать!")
        return

    if time.time() - boss_data.get("start_time", 0) > BOSS_TIMEOUT_SECONDS:
        send(peer_id, "Бой истёк. Напиши 'босс' чтобы начать нового.")
        return

    lines = [
        f"👹 {boss_data['name']} (ур. {boss_data['level']})",
        f"HP: {boss_data['current_hp']}/{boss_data['max_hp']}",
        f"Атака: {boss_data.get('attack', 0)}",
        f"Защита: {boss_data.get('defense', 0)}",
        "",
        f"Участников: {len(boss_data['participants'])}",
    ]
    
    if str(user_id) in boss_data["participants"]:
        my_damage = boss_data["participants"][str(user_id)]["damage"]
        lines.append(f"Твой урон: {my_damage}")
    
    send(peer_id, "\n".join(lines))


def leave_boss_fight(user_id, peer_id):
    """Покинуть бой с боссом"""
    boss_data = load_boss()

    if not boss_data.get("active"):
        send(peer_id, "Ты не участвуешь в бою.")
        return

    if str(user_id) not in boss_data["participants"]:
        send(peer_id, "Ты не участвуешь в этом бою.")
        return

    del boss_data["participants"][str(user_id)]
    save_boss(boss_data)
    
    send(peer_id, "Ты покинул бой с боссом.")


# ==================== ОБРАБОТЧИК КОМАНД ====================
def handle(user_id, peer_id, text):
    player = get_player(user_id)
    player["last_peer_id"] = peer_id
    save_players()

    command = text.lower().strip()

    if not command:
        return

    if command in ["старт", "start", "/start", "!start", "помощь", "help"]:
        send(peer_id, f"{player['name']}, добро пожаловать!\n\n{HELP_TEXT}")
        return

    if command in ["баланс", "balance", "!баланс"]:
        send(peer_id, f"Баланс: {player['balance']} монет.")
        return

    if command in ["id", "айди", "мой id"]:
        send(peer_id, f"Твой ID: {user_id}\nИспользуй его для вызова: вызов @id{user_id}")
        return

    if command in ["работа", "work", "!работа"]:
        now = int(time.time())
        wait_seconds = WORK_COOLDOWN_SECONDS - (now - player.get("last_work", 0))
        if wait_seconds > 0:
            send(peer_id, f"Отдохни ещё {wait_seconds} сек.")
            return
        earned = random.randint(20, 80)
        player["balance"] += earned
        player["last_work"] = now
        level_up = add_exp(player, 2)
        save_players()
        message = f"{player['name']}, ты заработал(а) {earned} монет."
        if level_up:
            message += f"\nНовый уровень: {player['level']}!"
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
            message = f"Выигрыш! Ты получаешь {prize} монет."
        else:
            message = f"Не повезло. Ты потерял(а) {amount} монет."
        add_exp(player, 1)
        save_players()
        send(peer_id, message)
        return

    if command in ["дуэль", "duel", "!дуэль"]:
        play_duel_vs_bot(player, peer_id)
        return

    if command in ["бонус", "bonus", "!бонус", "ежедневный бонус"]:
        claim_daily_bonus(player, peer_id)
        return

    if command in ["топ", "top", "!топ", "рейтинг", "rating"]:
        show_top(peer_id)
        return

    if command in ["профиль", "profile", "!профиль"]:
        cosmetic = ""
        if player.get("equipped") and player["equipped"].get("cosmetic"):
            cid = player["equipped"]["cosmetic"]
            if cid in ITEMS:
                cosmetic = f"\nУкрашение: {ITEM_EMOJI.get(cid, '')} {ITEMS[cid]['name']}"
        send(
            peer_id,
            "Профиль\n\n"
            f"Имя: {player['name']}\n"
            f"Уровень: {player['level']}\n"
            f"Опыт: {player['exp']}\n"
            f"Баланс: {player['balance']} монет\n"
            f"Серия бонусов: {player.get('bonus_streak', 0)} дн."
            f"{cosmetic}",
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

    # === PvP команды ===
    if command.startswith("вызов ") or command.startswith("pvp ") or command.startswith("дуэль @"):
        opponent_id = parse_user_id_from_mention(text)
        if opponent_id is None:
            send(peer_id, "Не удалось определить ID. Формат: вызов @id123456")
            return
        challenge_player(user_id, opponent_id, peer_id)
        return

    if command in ["принять", "accept"]:
        accept_duel(user_id, peer_id)
        return

    if command in ["отклонить", "decline", "отмена"]:
        decline_duel(user_id, peer_id)
        return

    # === Босс команды ===
    if command in ["босс", "boss", "!босс"]:
        start_boss_fight(user_id, peer_id)
        return

    if command in ["атака", "attack", "удар", "hit", "бить"]:
        attack_boss(user_id, peer_id)
        return

    if command in ["статус", "status", "босс статус"]:
        show_boss_status(user_id, peer_id)
        return

    if command in ["сдаться", "leave", "выйти"]:
        leave_boss_fight(user_id, peer_id)
        return

    # Неизвестная команда — молчим
    return