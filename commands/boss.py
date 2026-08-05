"""
Команды босса: начало боя, атака, статус, сдача, распределение наград.
"""
import time
import db
from config.boss import BOSS_LEVELS, BOSS_TIMEOUT_SECONDS
from utils.helpers import send, get_player_damage, get_player_defense, add_exp, get_name


def cmd_start_boss(api, peer_id, user_id):
    """Начать бой с боссом или присоединиться к нему."""
    boss = db.get_boss()
    
    if boss and boss.get("active"):
        # Проверка таймаута
        if boss.get("start_time") and (time.time() - boss["start_time"]) > BOSS_TIMEOUT_SECONDS:
            db.clear_boss()
            return _create_new_boss(api, peer_id, user_id)
        
        # Проверка участия
        if any(p["player_id"] == user_id for p in boss.get("participants", [])):
            send(api, peer_id, "Ты уже участвуешь! Пиши 'атака'.")
            return
        
        # Присоединение
        player = db.get_player(user_id, lambda uid: get_name(api, uid))
        boss["participants"].append({
            "player_id": user_id, 
            "name": player["name"], 
            "damage": 0, 
            "peer_id": peer_id
        })
        db.save_boss(boss)
        send(api, peer_id, f"Ты присоединился к бою с {boss['name']}!\nHP: {boss['current_hp']}/{boss['max_hp']}")
        return
        
    _create_new_boss(api, peer_id, user_id)


def _create_new_boss(api, peer_id, user_id):
    """Создать нового босса."""
    player = db.get_player(user_id, lambda uid: get_name(api, uid))
    
    # Уровень босса зависит от уровня игрока
    lvl = 1
    if player.get("level", 1) > 2: lvl = 2
    if player.get("level", 1) > 5: lvl = 3
    if player.get("level", 1) > 10: lvl = 4
    if player.get("level", 1) > 15: lvl = 5
    
    boss_template = BOSS_LEVELS[lvl]
    data = {
        "active": True, 
        "level": lvl, 
        "name": boss_template["name"], 
        "max_hp": boss_template["hp"], 
        "current_hp": boss_template["hp"],
        "attack": boss_template["attack"], 
        "defense": boss_template["defense"], 
        "start_time": time.time(),
        "participants": [{"player_id": user_id, "name": player["name"], "damage": 0, "peer_id": peer_id}]
    }
    db.save_boss(data)
    send(api, peer_id, f"👹 {boss_template['name']} (ур. {lvl}) появился!\nHP: {boss_template['hp']}\nПиши 'атака'!")
    
    # Уведомить других игроков
    try:
        all_players = db.get_all_peer_ids()
        for p in all_players:
            if p["user_id"] == user_id:
                continue
            if db.should_notify(p["user_id"], "boss", cooldown_hours=2):
                try:
                    send(api, p["last_peer_id"], 
                         f" Появился новый босс: {boss_template['name']} (ур. {lvl})!\n"
                         f"HP: {boss_template['hp']}\n"
                         f"Напиши: босс")
                    db.update_last_notification(p["user_id"], "boss")
                except Exception:
                    pass
    except Exception as e:
        print(f"Ошибка рассылки о боссе: {e}")


def cmd_attack_boss(api, peer_id, user_id):
    """Атаковать босса."""
    boss = db.get_boss()
    if not boss or not boss.get("active"):
        send(api, peer_id, "Нет активного боя. Напиши 'босс'.")
        return
        
    if boss.get("start_time") and (time.time() - boss["start_time"]) > BOSS_TIMEOUT_SECONDS:
        db.clear_boss()
        send(api, peer_id, "Бой истёк.")
        return
        
    participant = next((x for x in boss.get("participants", []) if x["player_id"] == user_id), None)
    if not participant:
        send(api, peer_id, "Ты не участвуешь! Напиши 'босс'.")
        return
        
    player = db.get_player(user_id, lambda uid: get_name(api, uid))
    
    # Урон игрока
    dmg = max(1, get_player_damage(player) - boss.get("defense", 0))
    boss["current_hp"] -= dmg
    participant["damage"] += dmg
    
    # Урон босса
    boss_dmg = max(1, boss.get("attack", 10) - get_player_defense(player))
    
    db.save_boss(boss)
    send(api, peer_id, f"Ты нанёс {dmg} урона {boss['name']}!\nHP: {max(0, boss['current_hp'])}/{boss['max_hp']}\nБосс атакует на {boss_dmg}.")
    
    if boss["current_hp"] <= 0:
        _defeat_boss(api, boss)


def _defeat_boss(api, boss):
    """Распределить награды за победу над боссом."""
    total_dmg = sum(p["damage"] for p in boss["participants"])
    if total_dmg == 0:
        total_dmg = 1  # Защита от деления на ноль
        
    msgs = [f"👹 {boss['name']} повержен!\n\nНаграды:"]
    
    for p in boss["participants"]:
        share = p["damage"] / total_dmg
        reward = int(BOSS_LEVELS[boss["level"]]["reward"] * share)
        exp = int(BOSS_LEVELS[boss["level"]]["exp"] * share)
        
        # Бонусы питомца
        pet_coin_bonus = db.get_pet_bonus(p["player_id"], "coins")
        if pet_coin_bonus > 0:
            reward = int(reward * (1 + pet_coin_bonus))
        pet_exp_bonus = db.get_pet_bonus(p["player_id"], "exp")
        if pet_exp_bonus > 0:
            exp = int(exp * (1 + pet_exp_bonus))
            
        # Бонусы клана
        clan = db.get_clan(p["player_id"])
        if clan:
            clan_coins_bonus = db.get_clan_bonus(clan["id"], "coins")
            if clan_coins_bonus > 0:
                reward = int(reward * (1 + clan_coins_bonus))
            clan_exp_bonus = db.get_clan_bonus(clan["id"], "exp")
            if clan_exp_bonus > 0:
                exp = int(exp * (1 + clan_exp_bonus))
            db.add_clan_exp(clan["id"], 15)
        
        pl = db.get_player(p["player_id"], lambda uid: get_name(api, uid))
        pl["balance"] += reward
        add_exp(pl, exp, clan)
        db.save_player(pl)
        
        db.update_daily_progress(p["player_id"], "boss", 1)
        db.add_season_points(p["player_id"], 20)
        
        achs = db.check_achievements_on_action(p["player_id"], pl, "boss_kill")
        ach_msg = "  " + ", ".join(achs) if achs else ""
        msgs.append(f"{p['name']}: +{reward}💰, +{exp}⭐ (урон: {p['damage']}){ach_msg}")
        
    boss["active"] = False
    db.save_boss(boss)
    
    for p in boss["participants"]:
        send(api, p["peer_id"], "\n".join(msgs))


def cmd_boss_status(api, peer_id, user_id):
    """Посмотреть статус текущего босса."""
    boss = db.get_boss()
    if not boss or not boss.get("active"):
        send(api, peer_id, "Нет активного боя.")
        return
        
    lines = [
        f"👹 {boss['name']} (ур. {boss['level']})", 
        f"HP: {boss['current_hp']}/{boss['max_hp']}", 
        f"Участников: {len(boss.get('participants', []))}"
    ]
    for p in boss.get("participants", []):
        if p["player_id"] == user_id:
            lines.append(f"Твой урон: {p['damage']}")
            
    send(api, peer_id, "\n".join(lines))


def cmd_leave_boss(api, peer_id, user_id):
    """Покинуть бой с боссом."""
    boss = db.get_boss()
    if not boss or not boss.get("active"):
        return
        
    boss["participants"] = [p for p in boss.get("participants", []) if p["player_id"] != user_id]
    db.save_boss(boss)
    send(api, peer_id, "Ты покинул бой.")