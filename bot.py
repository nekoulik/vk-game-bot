import os
import json
import random
import time

from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))

if not TOKEN or not GROUP_ID:
    raise SystemExit("Создай файл .env и укажи VK_TOKEN и VK_GROUP_ID")

DATA_FILE = "players.json"
WORK_COOLDOWN_SECONDS = 60
MIN_BET = 10

session = VkApi(token=TOKEN)
api = session.get_api()
longpoll = VkBotLongPoll(session, GROUP_ID)


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
профиль — показать профиль"""


def play_duel(player, peer_id):
    player_hp = 100
    bot_hp = 100
    log = []

    for round_number in range(1, 6):
        player_damage = random.randint(12, 25)
        bot_damage = random.randint(12, 25)
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

    send(peer_id, "⚔️ Дуэль с ботом:\n" + "\n".join(log[-3:]) + "\n\n" + result)


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

    if command in ["профиль", "profile", "!профиль"]:
        send(
            peer_id,
            "🧿 Профиль\n\n"
            f"Имя: {player['name']}\n"
            f"Уровень: {player['level']}\n"
            f"Опыт: {player['exp']}\n"
            f"Баланс: {player['balance']} монет",
        )
        return

    send(peer_id, "Не понял команду. Напиши: помощь")


def main():
    print("Бот запущен")
    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    message = event.obj.message
                    user_id = message.get("from_id")
                    peer_id = message.get("peer_id")
                    text = message.get("text", "")
                    if not user_id or not peer_id or not text:
                        continue
                    try:
                        handle(user_id, peer_id, text)
                    except Exception as e:
                        print("Ошибка в обработчике:", e)
        except Exception as e:
            print("Ошибка Long Poll:", e)
            time.sleep(2)


if __name__ == "__main__":
    main()