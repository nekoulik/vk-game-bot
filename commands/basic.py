"""
Основные команды бота: помощь, баланс, профиль, топ, работа, бонус, ставка, дуэль, магазин, квесты.
"""
import random
import time
from datetime import datetime, timedelta
from utils.helpers import send, get_name, format_number
from utils.keyboard import get_main_keyboard
import db
from config.shop import SHOP_ITEMS, WEAPONS, PETS


def cmd_help(api, peer_id):
    """Показать помощь с кнопками."""
    text = (
        "🎮 *Club Anicoke Bot*\n\n"
        "Выбери действие из меню ниже 👇\n\n"
        "💰 *Экономика:*\n"
        "  • баланс — проверить баланс\n"
        "  • работа — заработать монеты\n"
        "  • бонус — ежедневный бонус\n"
        "  • топ — топ игроков\n\n"
        "⚔️ *Сражения:*\n"
        "  • дуэль — сразиться с ботом\n"
        "  • босс — сразиться с боссом\n"
        "  • pvp — сразиться с игроком\n\n"
        "🛒 *Магазин:*\n"
        "  • магазин — купить предметы\n"
        "  • инвентарь — твои вещи\n\n"
        "📋 *Дополнительно:*\n"
        "  • квесты — ежедневные задания\n"
        "  • сезон — информация о сезоне\n"
        "  • игры — мини-игры\n"
        "  • клан — управление кланом\n"
        "  • помощь — это сообщение"
    )
    keyboard = get_main_keyboard()
    send(api, peer_id, text, keyboard=keyboard)


def cmd_balance(api, peer_id, player):
    """Показать баланс игрока."""
    balance = int(player.get("balance", 0))
    level = int(player.get("level", 1))
    
    if balance == -1:
        status = "🚫 Забанен"
    elif balance == -2:
        mute_until = player.get("mute_until", 0)
        try:
            mute_until = int(mute_until)
        except (ValueError, TypeError):
            mute_until = 0
        
        if mute_until and mute_until > int(time.time()):
            remaining = (mute_until - int(time.time())) // 60
            status = f"🔇 Мут ({remaining} мин)"
        else:
            status = "✅ Активен"
    else:
        status = "✅ Активен"
    
    text = (
        f"💰 *Твой баланс:*\n\n"
        f"👤 {player['name']}\n"
        f"⭐ Уровень: {level}\n"
        f"💵 Монеты: {format_number(balance)}\n"
        f"📊 Статус: {status}"
    )
    send(api, peer_id, text)


def cmd_profile(api, peer_id, player):
    """Показать профиль игрока."""
    balance = int(player.get("balance", 0))
    level = int(player.get("level", 1))
    exp = int(player.get("exp", 0))
    exp_to_next = level * 10
    
    text = (
        f"👤 *Профиль игрока:*\n\n"
        f"📛 Имя: {player['name']}\n"
        f"⭐ Уровень: {level}\n"
        f"💫 Опыт: {exp}/{exp_to_next}\n"
        f"💰 Баланс: {format_number(balance)} монет\n"
        f"🏆 Очки сезона: {int(player.get('season_points', 0))}\n"
        f"📅 Регистрация: {player.get('created_at', 'Неизвестно')[:10]}"
    )
    send(api, peer_id, text)


def cmd_top(api, peer_id):
    """Показать топ игроков."""
    top_players = db.get_top_players(10)
    
    if not top_players:
        send(api, peer_id, "🏆 Топ игроков пуст!")
        return
    
    lines = ["🏆 *Топ-10 игроков:*\n"]
    for i, p in enumerate(top_players, start=1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        lines.append(f"{medal} {p['name']} — ур. {p.get('level', 1)}, {format_number(p.get('balance', 0))}💰")
    
    send(api, peer_id, "\n".join(lines))


def cmd_work(api, peer_id, player):
    """Заработать монеты."""
    from config.settings import WORK_REWARD_MIN, WORK_REWARD_MAX
    from db.players import increment_daily_stat
    
    last_work = player.get("last_work", 0)
    try:
        last_work = int(last_work)
    except (ValueError, TypeError):
        last_work = 0
    
    now = int(time.time())
    cooldown = 3600  # 1 час
    
    if now - last_work < cooldown:
        remaining = (cooldown - (now - last_work)) // 60
        send(api, peer_id, f"⏱️ Ты уже работал! Попробуй через {remaining} мин.")
        return
    
    reward = random.randint(WORK_REWARD_MIN, WORK_REWARD_MAX)
    
    # ✅ 1. БОНУС ОТ ПИТОМЦА К МОНЕТАМ
    pet_bonus_coins = player.get("pet_bonus_coins", 0)
    if pet_bonus_coins > 0:
        reward = int(reward * (1 + pet_bonus_coins))
    
    # ✅ 2. БОНУС ОТ КЛАНА К МОНЕТАМ
    try:
        from db.clans import get_clan, get_clan_bonus
        clan = get_clan(player["user_id"])
        if clan:
            clan_bonus = get_clan_bonus(clan["id"], "coins")
            if clan_bonus > 0:
                reward = int(reward * (1 + clan_bonus))
    except Exception:
        pass
    
    player["balance"] = int(player.get("balance", 0)) + reward
    player["last_work"] = now
    
    # ✅ 3. НАЧИСЛЕНИЕ ОЧКОВ СЕЗОНА ЗА РАБОТУ
    player["season_points"] = player.get("season_points", 0) + 1
    
    db.save_player(player)
    
    increment_daily_stat(player["user_id"], "work", 1)
    
    # Формируем текст бонусов
    bonuses = []
    if pet_bonus_coins > 0:
        bonuses.append(f"питомец +{int(pet_bonus_coins*100)}%")
    
    bonus_text = f" (вкл. {', '.join(bonuses)})" if bonuses else ""
    send(api, peer_id, f"💼 Ты поработал и заработал {reward} монет! (+1 очко сезона){bonus_text}")


def cmd_bonus(api, peer_id, player):
    """Получить ежедневный бонус."""
    from config.settings import DAILY_BONUS
    from db.players import increment_daily_stat
    
    last_bonus = player.get("last_bonus", "")
    today = time.strftime("%Y-%m-%d")
    
    if last_bonus == today:
        send(api, peer_id, "🎁 Ты уже получил бонус сегодня! Приходи завтра.")
        return
    
    streak = player.get("bonus_streak", 0)
    try:
        streak = int(streak)
    except (ValueError, TypeError):
        streak = 0
    
    streak += 1
    bonus = DAILY_BONUS + (streak * 10)
    
    player["balance"] = int(player.get("balance", 0)) + bonus
    player["last_bonus"] = today
    player["bonus_streak"] = streak
    db.save_player(player)
    
    increment_daily_stat(player["user_id"], "bonus", 1)
    
    send(api, peer_id, f"🎁 Ежедневный бонус: {bonus} монет!\n🔥 Серия: {streak} дней")


def cmd_bet(api, peer_id, player, command):
    """Сделать ставку (бросок кубика)."""
    parts = command.split()
    
    if len(parts) < 2:
        send(api, peer_id, "🎲 Формат: ставка <сумма> (минимум 50)")
        return
    
    try:
        bet_amount = int(parts[1])
    except ValueError:
        send(api, peer_id, "❌ Сумма должна быть числом!")
        return
    
    if bet_amount < 50:
        send(api, peer_id, "❌ Минимальная ставка: 50 монет")
        return
    
    balance = int(player.get("balance", 0))
    if bet_amount > balance:
        send(api, peer_id, f"❌ Недостаточно монет! У тебя: {balance}")
        return
    
    player_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)
    
    if player_roll > bot_roll:
        player["balance"] = balance + bet_amount
        result = f"🎉 Ты выиграл {bet_amount} монет!"
    elif player_roll < bot_roll:
        player["balance"] = balance - bet_amount
        result = f"😔 Ты проиграл {bet_amount} монет!"
    else:
        result = "🤝 Ничья! Ставка возвращена."
    
    db.save_player(player)
    
    text = (
        f"🎲 *Бросок кубика:*\n\n"
        f"🎯 Твой бросок: {player_roll}\n"
        f"🤖 Бросок бота: {bot_roll}\n\n"
        f"{result}\n"
        f"💰 Баланс: {format_number(player['balance'])}"
    )
    send(api, peer_id, text)


def cmd_duel(api, peer_id, user_id, player, command):
    """Дуэль с ботом (бросок кубика)."""
    from db.players import increment_daily_stat
    
    balance = int(player.get("balance", 0))
    
    if balance <= 0:
        player_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        
        if player_roll > bot_roll:
            reward = 25
            player["balance"] = balance + reward
            db.save_player(player)
            result = f"🎉 Ты победил бота! +{reward} монет"
            increment_daily_stat(player["user_id"], "duels_won", 1)
        elif player_roll < bot_roll:
            result = "😔 Ты проиграл боту. Монеты не списаны (баланс 0)."
        else:
            result = "🤝 Ничья!"
        
        text = (f"⚔️ *Дуэль с ботом:*\n\n🎯 Твой бросок: {player_roll}\n🤖 Бросок бота: {bot_roll}\n\n{result}\n💰 Баланс: {format_number(player['balance'])}")
        send(api, peer_id, text)
        return
    
    bet = 50
    player_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)
    
    if player_roll > bot_roll:
        player["balance"] = balance + bet
        db.save_player(player)
        result = f"🎉 Ты победил бота! +{bet} монет"
        increment_daily_stat(player["user_id"], "duels_won", 1)
    elif player_roll < bot_roll:
        player["balance"] = balance - bet
        db.save_player(player)
        result = f"😔 Ты проиграл боту! -{bet} монет"
    else:
        result = "🤝 Ничья! Ставка возвращена."
    
    text = (f"⚔️ *Дуэль с ботом (ставка {bet} монет):*\n\n🎯 Твой бросок: {player_roll}\n🤖 Бросок бота: {bot_roll}\n\n{result}\n💰 Баланс: {format_number(player['balance'])}")
    send(api, peer_id, text)


def cmd_shop(api, peer_id):
    """Показать магазин с категориями."""
    potions_list = [f"{num}. {item['emoji']} {item['name']} — {item['price']} монет" for num, item in SHOP_ITEMS.items() if item['category'] == 'potions']
    weapons_list = [f"{num}. {item['emoji']} {item['name']} — {item['price']} монет (+{item['damage']} урон)" for num, item in SHOP_ITEMS.items() if item['category'] == 'weapons']
    pets_list = [f"{num}. {item['emoji']} {item['name']} — {item['price']} монет ({item['bonus']})" for num, item in SHOP_ITEMS.items() if item['category'] == 'pets']
    
    text = (
        f"🛒 *Магазин предметов*\n\n"
        f"💊 *Зелья:*\n" + "\n".join(potions_list) + "\n\n"
        f"⚔️ *Оружие:*\n" + "\n".join(weapons_list) + "\n\n"
        f"🐾 *Питомцы:*\n" + "\n".join(pets_list) + "\n\n"
        f"💡 Формат: *купить <номер>*\n"
        f"💡 Формат: *экипировать <номер>* (для оружия и питомцев)"
    )
    send(api, peer_id, text)


def cmd_buy(api, peer_id, player, command):
    """Купить предмет из магазина."""
    parts = command.split()
    
    if len(parts) < 2:
        send(api, peer_id, "🛒 Формат: купить <номер>\nПример: купить 1")
        return
    
    try:
        item_number = int(parts[1])
    except ValueError:
        send(api, peer_id, "❌ Номер должен быть числом!")
        return
    
    if item_number not in SHOP_ITEMS:
        send(api, peer_id, f"❌ Такого предмета нет! Доступные номера: {list(SHOP_ITEMS.keys())}")
        return
    
    item = SHOP_ITEMS[item_number]
    balance = int(player.get("balance", 0))
    
    if balance < item["price"]:
        send(api, peer_id, f"❌ Недостаточно монет! Нужно {item['price']}, у тебя {balance}")
        return
    
    if item["category"] in ["weapons", "pets"]:
        try:
            from db.items import get_inventory
            inventory = get_inventory(player["user_id"])
            for inv_item in inventory:
                if inv_item["item_id"] == item["item_id"]:
                    send(api, peer_id, f"❌ У тебя уже есть {item['emoji']} {item['name']}!")
                    return
        except:
            pass
    
    player["balance"] = balance - item["price"]
    db.save_player(player)
    
    try:
        from db.items import add_item
        add_item(player["user_id"], item["item_id"], 1)
        
        if item["category"] == "weapons":
            if not player.get("equipped_weapon"):
                player["equipped_weapon"] = item["item_id"]
                db.save_player(player)
                send(api, peer_id, f"✅ Куплено и автоматически экипировано: {item['emoji']} {item['name']}!\n💰 Осталось: {player['balance']}\n⚔️ Урон: +{item['damage']}")
            else:
                send(api, peer_id, f"✅ Куплено: {item['emoji']} {item['name']}!\n💰 Осталось: {player['balance']}\n💡 Напиши *экипировать {item_number}* чтобы надеть")
        elif item["category"] == "pets":
            send(api, peer_id, f"✅ Куплено: {item['emoji']} {item['name']}!\n💰 Осталось: {player['balance']}\n💡 Напиши *экипировать {item_number}* чтобы активировать питомца")
        else:
            send(api, peer_id, f"✅ Куплено: {item['emoji']} {item['name']}!\n💰 Осталось: {player['balance']}")
    except Exception as e:
        send(api, peer_id, f"⚠️ Предмет куплен, но не добавлен в инвентарь: {e}")


def cmd_equip(api, peer_id, player, command):
    """Экипировать оружие или активировать питомца."""
    parts = command.split()
    
    if len(parts) < 2:
        send(api, peer_id, "⚙️ Формат: экипировать <номер>\nПример: экипировать 5")
        return
    
    try:
        item_number = int(parts[1])
    except ValueError:
        send(api, peer_id, "❌ Номер должен быть числом!")
        return
    
    if item_number not in SHOP_ITEMS:
        send(api, peer_id, f"❌ Такого предмета нет! Доступные номера: {list(SHOP_ITEMS.keys())}")
        return
    
    item = SHOP_ITEMS[item_number]
    
    if item["category"] not in ["weapons", "pets"]:
        send(api, peer_id, "❌ Этот предмет нельзя экипировать (только оружие и питомцы)")
        return
    
    try:
        from db.items import get_inventory
        inventory = get_inventory(player["user_id"])
        has_item = any(inv["item_id"] == item["item_id"] for inv in inventory)
        
        if not has_item:
            send(api, peer_id, f"❌ У тебя нет {item['emoji']} {item['name']}!")
            return
    except:
        send(api, peer_id, "⚠️ Ошибка проверки инвентаря")
        return
    
    if item["category"] == "weapons":
        old_weapon_id = player.get("equipped_weapon")
        player["equipped_weapon"] = item["item_id"]
        db.save_player(player)
        
        old_weapon_data = next((v for v in SHOP_ITEMS.values() if v["item_id"] == old_weapon_id), None)
        old_name = old_weapon_data["name"] if old_weapon_data else "ничего"
        
        send(api, peer_id, f"⚔️ Экипировано: {item['emoji']} {item['name']}!\n💥 Урон: +{item['damage']}\n(Было: {old_name})")
    
    elif item["category"] == "pets":
        old_pet_id = player.get("active_pet")
        player["active_pet"] = item["item_id"]
        
        pet_bonuses = {
            "pet_cat": {"coins": 0.05, "damage": 0},
            "pet_dog": {"coins": 0, "damage": 0.10},
            "pet_dragon": {"coins": 0.20, "damage": 0},
            "pet_phoenix": {"coins": 0, "damage": 0.30},
            "pet_unicorn": {"coins": 0.50, "damage": 0.50},
        }
        
        bonuses = pet_bonuses.get(item["item_id"], {"coins": 0, "damage": 0})
        player["pet_bonus_coins"] = bonuses["coins"]
        player["pet_bonus_damage"] = bonuses["damage"]
        
        db.save_player(player)
        
        old_pet_data = next((v for v in SHOP_ITEMS.values() if v["item_id"] == old_pet_id), None)
        old_name = old_pet_data["name"] if old_pet_data else "никто"
        
        send(api, peer_id, f"🐾 Питомец активирован: {item['emoji']} {item['name']}!\n{item['bonus']}\n(Был: {old_name})")


def cmd_inventory(api, peer_id, player):
    """Показать инвентарь игрока."""
    try:
        from db.items import get_inventory
        from collections import defaultdict
        
        inventory = get_inventory(player["user_id"])
        
        lines = ["🎒 *Твой инвентарь:*\n"]
        
        equipped_weapon_id = player.get("equipped_weapon")
        active_pet_id = player.get("active_pet")
        
        if equipped_weapon_id:
            weapon_data = next((v for v in SHOP_ITEMS.values() if v["item_id"] == equipped_weapon_id), None)
            if weapon_data:
                lines.append(f"⚔️ *Оружие:* {weapon_data['emoji']} {weapon_data['name']} (+{weapon_data['damage']} урон)\n")
        
        if active_pet_id:
            pet_data = next((v for v in SHOP_ITEMS.values() if v["item_id"] == active_pet_id), None)
            if pet_data:
                lines.append(f"🐾 *Питомец:* {pet_data['emoji']} {pet_data['name']} ({pet_data['bonus']})\n")
        
        if not inventory:
            lines.append("📦 Предметов нет")
        else:
            grouped_items = defaultdict(int)
            for inv_item in inventory:
                item_id = inv_item['item_id']
                quantity = inv_item.get('quantity', 1)
                grouped_items[item_id] += quantity
            
            lines.append("\n📦 *Предметы:*")
            for item_id, total_quantity in grouped_items.items():
                item_data = next((v for v in SHOP_ITEMS.values() if v["item_id"] == item_id), None)
                if item_data:
                    lines.append(f"• {item_data['emoji']} {item_data['name']} x{total_quantity}")
                else:
                    lines.append(f"• {item_id} x{total_quantity}")
        
        send(api, peer_id, "\n".join(lines))
    except Exception as e:
        send(api, peer_id, f"⚠️ Ошибка получения инвентаря: {e}")


def cmd_use(api, peer_id, player, command):
    """Использовать предмет из инвентаря."""
    parts = command.split()
    
    if len(parts) < 2:
        send(api, peer_id, "🎒 Формат: использовать <номер>\n\nПример: использовать 1")
        return
    
    try:
        item_number = int(parts[1])
    except ValueError:
        send(api, peer_id, "❌ Номер должен быть числом!")
        return
    
    try:
        from db.items import get_inventory
        inventory = get_inventory(player["user_id"])
    except Exception as e:
        send(api, peer_id, f"⚠️ Ошибка получения инвентаря: {e}")
        return
    
    if not inventory:
        send(api, peer_id, "🎒 Инвентарь пуст!")
        return
    
    item_mapping = {1: "health_potion", 2: "strength_potion", 3: "speed_potion"}
    
    if item_number not in item_mapping:
        send(api, peer_id, "❌ Такого предмета нет в инвентаре!")
        return
    
    item_id = item_mapping[item_number]
    
    target_item = None
    for item in inventory:
        if item['item_id'] == item_id and item['quantity'] > 0:
            target_item = item
            break
    
    if not target_item:
        send(api, peer_id, "❌ У тебя нет этого предмета!")
        return
    
    item_names = {"health_potion": "💚 Зелье здоровья", "strength_potion": "🛡️ Зелье силы", "speed_potion": "⚡ Зелье скорости"}
    item_name = item_names.get(item_id, item_id)
    
    if item_id == "health_potion":
        send(api, peer_id, f"💚 Ты использовал {item_name}!\n❤️ Здоровье восстановлено на 50!\n⏳ Эффект: мгновенный")
    elif item_id == "strength_potion":
        send(api, peer_id, f"🛡️ Ты использовал {item_name}!\n⚔️ Сила увеличена на 10 минут!\n⏳ Осталось времени: 10 мин")
    elif item_id == "speed_potion":
        send(api, peer_id, f"⚡ Ты использовал {item_name}!\n💨 Скорость увеличена на 10 минут!\n⏳ Осталось времени: 10 мин")
    
    try:
        from db.items import remove_item
        remove_item(player["user_id"], item_id, 1)
    except Exception as e:
        print(f"Ошибка удаления предмета: {e}")


def cmd_use_all(api, peer_id, player, command):
    """Использовать все предметы одного типа."""
    parts = command.split()
    
    if len(parts) < 2:
        send(api, peer_id, "🎒 Формат: использовать все <номер>\n\nПример: использовать все 1")
        return
    
    try:
        item_number = int(parts[1])
    except ValueError:
        send(api, peer_id, "❌ Номер должен быть числом!")
        return
    
    try:
        from db.items import get_inventory
        inventory = get_inventory(player["user_id"])
    except Exception as e:
        send(api, peer_id, f"⚠️ Ошибка получения инвентаря: {e}")
        return
    
    if not inventory:
        send(api, peer_id, "🎒 Инвентарь пуст!")
        return
    
    item_mapping = {1: "health_potion", 2: "strength_potion", 3: "speed_potion"}
    
    if item_number not in item_mapping:
        send(api, peer_id, "❌ Такого предмета нет в инвентаре!")
        return
    
    item_id = item_mapping[item_number]
    
    target_item = None
    for item in inventory:
        if item['item_id'] == item_id:
            target_item = item
            break
    
    if not target_item or target_item['quantity'] == 0:
        send(api, peer_id, "❌ У тебя нет этого предмета!")
        return
    
    quantity = target_item['quantity']
    
    try:
        from db.items import remove_item
        remove_item(player["user_id"], item_id, quantity)
        send(api, peer_id, f"✅ Использовано {quantity} предметов!")
    except Exception as e:
        send(api, peer_id, f"⚠️ Ошибка: {e}")


def cmd_season(api, peer_id, user_id, player):
    """Показать информацию о текущем сезоне."""
    current_season = player.get("current_season", 1)
    season_points = player.get("season_points", 0)
    
    # Даты сезона (пример: 1 месяц)
    season_start = datetime(2026, 8, 1)
    season_end = season_start + timedelta(days=30)
    today = datetime.now()
    
    days_left = (season_end - today).days
    if days_left < 0:
        days_left = 0
    
    # Получаем топ сезона
    conn = db.get_conn()
    try:
        top_season = conn.execute(
            "SELECT user_id, name, season_points FROM players ORDER BY season_points DESC LIMIT 10"
        ).fetchall()
        top_season = [dict(r) for r in top_season]
    finally:
        conn.close()
    
    # Находим место игрока
    player_rank = None
    for i, p in enumerate(top_season, start=1):
        if p["user_id"] == user_id:
            player_rank = i
            break
    
    if not player_rank:
        player_rank = len(top_season) + 1
    
    # Следующая награда
    next_reward = None
    if season_points < 1000:
        next_reward = 1000
    elif season_points < 2500:
        next_reward = 2500
    elif season_points < 5000:
        next_reward = 5000
    
    # Формируем текст
    lines = [
        f"🏆 *Сезон {current_season}*",
        f"📅 {season_start.strftime('%d.%m.%Y')} — {season_end.strftime('%d.%m.%Y')}",
        f"⏳ Осталось дней: {days_left}\n",
        f"👤 *Твой прогресс:*",
        f"⭐ Очки: {season_points}",
        f"📊 Место в рейтинге: #{player_rank}",
    ]
    
    if next_reward:
        lines.append(f"🎯 До следующей награды: {next_reward - season_points} очков\n")
    
    lines.append("🏅 *Награды сезона:*")
    lines.append("🥇 1 место — 10000 монет + титул 'Чемпион'")
    lines.append("🥈 2 место — 5000 монет + титул 'Призёр'")
    lines.append("🥉 3 место — 2500 монет + титул 'Бронза'")
    lines.append("4-10 место — 1000 монет\n")
    
    lines.append("🏆 *Топ-10 сезона:*")
    for i, p in enumerate(top_season[:10], start=1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        lines.append(f"{medal} {p['name']} — {p['season_points']} очков")
    
    lines.append("\n💡 *Как заработать очки:*")
    lines.append("• Работа — +1 очко")
    lines.append("• Победа в дуэли — +5 очков")
    lines.append("• Убийство босса — +10 очков")
    lines.append("• Победа в PvP — +15 очков")
    
    send(api, peer_id, "\n".join(lines))