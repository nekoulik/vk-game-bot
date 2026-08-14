"""Команды для работы с квестами."""
from utils.helpers import send, format_number
from config.quests import DAILY_QUESTS
from db.players import check_and_reset_daily_quests, save_player
import db


def cmd_quests(api, peer_id, player):
    """Показать статус квестов."""
    player = check_and_reset_daily_quests(player)
    
    lines = ["📋 *Ежедневные задания:*\n"]
    
    for q_key, q_data in DAILY_QUESTS.items():
        # Получаем текущий прогресс по ключу квеста
        stat_column = {
            "work": "daily_work",
            "duels": "daily_duels",
            "boss": "daily_boss_damage",
            "bonus": "daily_bonus",
            "games": "daily_games",
        }.get(q_key, None)
        
        if stat_column:
            current = player.get(stat_column, 0)
        else:
            current = 0
        
        target = q_data["target"]
        is_completed = current >= target
        status = "✅" if is_completed else ""
        
        lines.append(f"{status} {q_data['name']} ({current}/{target}) — {q_data['reward_coins']}💰")
    
    # Проверяем можно ли забрать награды
    if player.get("daily_quest_claimed", 0) == 1:
        lines.append("\n✅ Награды уже получены сегодня.")
        lines.append("🕐 Завтра будут новые задания!")
    else:
        lines.append("\n💡 Напиши *выполнить квесты* чтобы забрать награды за завершённые.")
    
    send(api, peer_id, "\n".join(lines))


def cmd_claim_quests(api, peer_id, player):
    """Забрать награды за выполненные квесты."""
    player = check_and_reset_daily_quests(player)
    
    # Проверяем уже ли забрали
    if player.get("daily_quest_claimed", 0) == 1:
        send(api, peer_id, "✅ Награды уже получены сегодня!\n Приходи завтра за новыми.")
        return
    
    total_coins = 0
    total_exp = 0
    completed = []
    
    for q_key, q_data in DAILY_QUESTS.items():
        stat_column = {
            "work": "daily_work",
            "duels": "daily_duels",
            "boss": "daily_boss_damage",
            "bonus": "daily_bonus",
            "games": "daily_games",
        }.get(q_key, None)
        
        if stat_column:
            current = player.get(stat_column, 0)
        else:
            current = 0
        
        target = q_data["target"]
        
        if current >= target:
            total_coins += q_data["reward_coins"]
            total_exp += q_data["reward_exp"]
            completed.append(f"✅ {q_data['name']} (+{q_data['reward_coins']}💰)")
    
    if not completed:
        send(api, peer_id, "❌ Ни один квест ещё не выполнен.\nПродолжай играть чтобы выполнить задания!")
        return
    
    # Начисляем награды
    player["balance"] = int(player.get("balance", 0)) + total_coins
    player["exp"] = int(player.get("exp", 0)) + total_exp
    player["daily_quest_claimed"] = 1
    
    # Проверяем повышение уровня
    old_level = int(player.get("level", 1))
    while player["exp"] >= player["level"] * 10:
        player["exp"] -= player["level"] * 10
        player["level"] = int(player["level"]) + 1
    
    try:
        save_player(player)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения после квестов: {e}")
    
    # Формируем сообщение
    msg = "🎉 *Квесты выполнены!*\n\n"
    msg += "\n".join(completed)
    msg += f"\n\n💰 Всего: +{total_coins} монет"
    msg += f"\n⭐ Всего: +{total_exp} опыта"
    
    # ✅ Показываем новый уровень только если он повысился
    if player["level"] > old_level:
        msg += f"\n📊 Новый уровень: {player['level']}!"
    
    msg += f"\n\n Текущий баланс: {format_number(player['balance'])}"
    
    send(api, peer_id, msg)