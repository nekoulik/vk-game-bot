"""Функции для работы с квестами и достижениями."""
from datetime import datetime
from db.base import get_conn
from config.quests import DAILY_QUESTS, ACHIEVEMENTS
from db.players import save_player


def claim_daily_quests(player):
    """Забрать награды за ежедневные квесты."""
    if player.get("daily_quest_claimed", 0) == 1:
        return False, "Квесты уже выполнены сегодня!"
    
    today = datetime.now().strftime("%Y-%m-%d")
    if player.get("last_quest_date") != today:
        from db.players import check_and_reset_daily_quests
        player = check_and_reset_daily_quests(player)

    total_coins = 0
    total_exp = 0
    completed = []

    for q_type, q_data in DAILY_QUESTS.items():
        if q_type == "duels":
            current = player.get("daily_duels", 0)
        elif q_type == "boss":
            current = player.get("daily_boss_kills", 0)
        elif q_type == "coins":
            current = player.get("daily_coins_earned", 0)
        else:
            current = 0

        if current >= q_data["target"]:
            total_coins += q_data["reward_coins"]
            total_exp += q_data["reward_exp"]
            completed.append(f"✅ {q_data['name']} (+{q_data['reward_coins']}💰, +{q_data['reward_exp']}⭐)")

    if not completed:
        return False, "Ни один квест ещё не выполнен. Продолжай играть!"

    player["balance"] += total_coins
    player["exp"] += total_exp
    while player["exp"] >= player["level"] * 10:
        player["exp"] -= player["level"] * 10
        player["level"] += 1
    
    player["daily_quest_claimed"] = 1
    save_player(player)
    
    msg = "🎉 Квесты выполнены!\n\n" + "\n".join(completed)
    msg += f"\n\n💰 Всего: +{total_coins} монет\n⭐ Всего: +{total_exp} опыта"
    return True, msg


def get_daily_quests_status(player):
    """Получить статус ежедневных квестов."""
    today = datetime.now().strftime("%Y-%m-%d")
    if player.get("last_quest_date") != today:
        from db.players import check_and_reset_daily_quests
        player = check_and_reset_daily_quests(player)

    lines = [" Ежедневные задания:\n"]
    for q_type, q_data in DAILY_QUESTS.items():
        if q_type == "duels":
            current = player.get("daily_duels", 0)
        elif q_type == "boss":
            current = player.get("daily_boss_kills", 0)
        elif q_type == "coins":
            current = player.get("daily_coins_earned", 0)
        else:
            current = 0
            
        target = q_data["target"]
        status = "✅" if current >= target else ""
        lines.append(f"{status} {q_data['name']} ({current}/{target}) — {q_data['reward_coins']}💰, {q_data['reward_exp']}⭐")
    
    if player.get("daily_quest_claimed", 0) == 1:
        lines.append("\n✅ Награды уже получены сегодня.")
    else:
        lines.append("\n💡 Напиши 'выполнить квесты' чтобы забрать награды за завершённые.")
    
    return "\n".join(lines)


def unlock_achievement(user_id, ach_id, player_name):
    """Разблокировать достижение."""
    conn = get_conn()
    try:
        exists = conn.execute("SELECT 1 FROM achievements WHERE user_id = ? AND achievement_id = ?", (user_id, ach_id)).fetchone()
        if exists:
            return None
        now = datetime.now().isoformat()
        conn.execute("INSERT INTO achievements (user_id, achievement_id, unlocked_at) VALUES (?, ?, ?)", (user_id, ach_id, now))
        conn.commit()
        return ACHIEVEMENTS.get(ach_id, {}).get("name", ach_id)
    finally:
        conn.close()


def get_achievements_list(user_id):
    """Получить список достижений игрока."""
    conn = get_conn()
    try:
        unlocked = [row["achievement_id"] for row in conn.execute("SELECT achievement_id FROM achievements WHERE user_id = ?", (user_id,)).fetchall()]
        lines = ["🏆 Достижения:\n"]
        for ach_id, data in ACHIEVEMENTS.items():
            if ach_id in unlocked:
                lines.append(f"✅ {data['name']}: {data['desc']}")
            else:
                lines.append(f"🔒 {data['name']}: {data['desc']}")
        return "\n".join(lines)
    finally:
        conn.close()


def check_achievements_on_action(user_id, player, action):
    """Проверить достижения после действия."""
    new_achs = []
    if action == "duel_win":
        player["total_duels_won"] = player.get("total_duels_won", 0) + 1
        if player["total_duels_won"] >= 1:
            name = unlock_achievement(user_id, "first_blood", player["name"])
            if name: new_achs.append(name)
    elif action == "rich":
        if player["balance"] >= 1000:
            name = unlock_achievement(user_id, "rich", player["name"])
            if name: new_achs.append(name)
    elif action == "boss_kill":
        player["total_boss_kills"] = player.get("total_boss_kills", 0) + 1
        if player["total_boss_kills"] >= 3:
            name = unlock_achievement(user_id, "boss_slayer", player["name"])
            if name: new_achs.append(name)
    
    if new_achs:
        save_player(player)
    return new_achs