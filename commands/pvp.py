"""
PvP-дуэли между игроками.
"""
import random
from utils.helpers import send, get_name, format_number
import db


def cmd_challenge_pvp(api, peer_id, user_id, player, command):
    """Вызвать игрока на PvP-дуэль."""
    parts = command.split()
    
    if len(parts) < 3:
        send(api, peer_id, "⚔️ Формат: вызов <id игрока> <ставка>\nПример: вызов 123456 100")
        return
    
    try:
        target_id = int(parts[1])
        stake = int(parts[2])
    except ValueError:
        send(api, peer_id, "❌ ID и ставка должны быть числами!")
        return
    
    # Проверки
    if target_id == user_id:
        send(api, peer_id, "❌ Нельзя вызвать себя!")
        return
    
    if stake < 50:
        send(api, peer_id, "❌ Минимальная ставка: 50 монет")
        return
    
    balance = int(player.get("balance", 0))
    if balance < stake:
        send(api, peer_id, f"❌ Недостаточно монет! Нужно {stake}, у тебя {balance}")
        return
    
    # Проверяем, существует ли игрок
    target_player = db.get_player(target_id, lambda uid: f"Игрок {uid}")
    if not target_player:
        send(api, peer_id, "❌ Игрок не найден!")
        return
    
    # Создаём вызов
    challenge_id, error = db.duels.create_pvp_challenge(user_id, target_id, stake)
    
    if error:
        send(api, peer_id, f"❌ {error}")
        return
    
    target_name = target_player.get("name", f"Игрок {target_id}")
    
    # Уведомляем вызывающего
    send(api, peer_id, f"⚔️ Ты вызвал {target_name} на дуэль!\n💰 Ставка: {stake} монет\n\nОн должен написать *принять* чтобы согласиться.\n💡 Чтобы отменить вызов — напиши *отменить*")
    
    # Пытаемся уведомить вызванного (если он в той же беседе — сработает)
    try:
        send(
            api, target_id,
            f"⚔️ {player['name']} вызывает тебя на дуэль!\n"
            f"💰 Ставка: {stake} монет\n\n"
            f"Напиши *принять* чтобы согласиться или *отклонить* чтобы отказаться."
        )
    except Exception:
        pass


def cmd_accept_pvp(api, peer_id, user_id, player):
    """Принять PvP-вызов."""
    challenge = db.duels.get_pvp_challenge_for_user(user_id)
    
    if not challenge:
        send(api, peer_id, "❌ У тебя нет активных вызовов!")
        return
    
    stake = challenge["stake"]
    balance = int(player.get("balance", 0))
    
    if balance < stake:
        send(api, peer_id, f"❌ Недостаточно монет для принятия вызова! Нужно {stake}, у тебя {balance}")
        return
    
    # Принимаем вызов
    challenge_data, error = db.duels.accept_pvp_challenge(challenge["id"], user_id)
    
    if error:
        send(api, peer_id, f"❌ {error}")
        return
    
    challenger_name = get_name(api, challenge["challenger_id"])
    
    send(api, peer_id, f"✅ Ты принял вызов от {challenger_name}!\n💰 Ставка: {stake} монет\n\n⚔️ Напиши *бой* чтобы начать сражение.")


def cmd_decline_pvp(api, peer_id, user_id):
    """Отклонить PvP-вызов."""
    challenge = db.duels.get_pvp_challenge_for_user(user_id)
    
    if not challenge:
        send(api, peer_id, "❌ У тебя нет активных вызовов!")
        return
    
    db.duels.decline_pvp_challenge(challenge["id"], user_id)
    
    challenger_name = get_name(api, challenge["challenger_id"])
    send(api, peer_id, f"❌ Ты отклонил вызов от {challenger_name}.")


def cmd_cancel_pvp(api, peer_id, user_id):
    """Отменить свой PvP-вызов."""
    success, error = db.duels.cancel_pvp_challenge(user_id)
    
    if error:
        send(api, peer_id, f"❌ {error}")
        return
    
    send(api, peer_id, "✅ Ты отменил свой вызов.")


def cmd_pvp_battle(api, peer_id, user_id, player):
    """Начать PvP-бой."""
    challenge = db.duels.get_pvp_accepted_challenge(user_id)
    
    if not challenge:
        send(api, peer_id, "❌ Нет активного боя! Сначала нужно принять вызов.")
        return
    
    # Начинаем бой
    result, error = db.duels.start_pvp_battle(challenge["id"])
    
    if error:
        send(api, peer_id, f"❌ {error}")
        return
    
    challenger_name = get_name(api, challenge["challenger_id"])
    target_name = get_name(api, challenge["target_id"])
    stake = challenge["stake"]
    
    if result["winner_id"]:
        winner_name = get_name(api, result["winner_id"])
        text = (
            f"⚔️ *PvP-бой завершён!*\n\n"
            f"👤 {challenger_name} бросил: {result['challenger_roll']}\n"
            f"👤 {target_name} бросил: {result['target_roll']}\n\n"
            f"🏆 Победитель: {winner_name}\n"
            f"💰 Выигрыш: {stake * 2} монет!"
        )
    else:
        text = (
            f"🤝 *PvP-бой завершён!*\n\n"
            f"👤 {challenger_name} бросил: {result['challenger_roll']}\n"
            f"👤 {target_name} бросил: {result['target_roll']}\n\n"
            f"🤝 Ничья! Ставки возвращены."
        )
    
    send(api, peer_id, text)


def cmd_pvp_status(api, peer_id, user_id):
    """Показать статус PvP-вызовов."""
    # Входящие вызовы
    incoming = db.duels.get_pvp_challenge_for_user(user_id)
    
    # Исходящие вызовы
    outgoing = db.duels.get_pvp_outgoing_challenge(user_id)
    
    lines = ["⚔️ *PvP-статус:*\n"]
    
    if incoming:
        challenger_name = get_name(api, incoming["challenger_id"])
        lines.append(f"📨 Входящий вызов от {challenger_name}\n   💰 Ставка: {incoming['stake']} монет\n   Напиши *принять* или *отклонить*")
    else:
        lines.append("📨 Нет входящих вызовов")
    
    if outgoing:
        target_name = get_name(api, outgoing["target_id"])
        lines.append(f"\n📤 Исходящий вызов к {target_name}\n   💰 Ставка: {outgoing['stake']} монет\n   Напиши *отменить* чтобы отменить")
    else:
        lines.append("\n📤 Нет исходящих вызовов")
    
    # ✅ ОПИСАНИЕ КОМАНД PvP
    lines.append("\n\n📋 *PvP команды:*\n")
    lines.append("⚔️ *Вызвать игрока:*\n")
    lines.append("  • вызов <id> <ставка>\n")
    lines.append("  • Пример: вызов 123456 100\n\n")
    lines.append("📩 *Принять/отклонить:*\n")
    lines.append("  • принять — согласиться на дуэль\n")
    lines.append("  • отклонить — отказаться\n\n")
    lines.append("⚔️ *Начать бой:*\n")
    lines.append("  • бой — начать сражение\n\n")
    lines.append("📊 *Статус:*\n")
    lines.append("  • pvp — показать статус вызовов\n\n")
    lines.append("💡 *Как играть:*\n")
    lines.append("1. Вызови игрока: вызов <id> <ставка>\n")
    lines.append("2. Игрок пишет: принять\n")
    lines.append("3. Оба пишут: бой\n")
    lines.append("4. Кто больше выбросит (1-100) — победил!\n")
    lines.append("💰 Победитель забирает x2 ставки")
    
    send(api, peer_id, "\n".join(lines))