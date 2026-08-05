"""
Административные команды: статистика, управление игроками, сбросы, рассылка.
"""
import db
from utils.helpers import send, get_name


def cmd_admin_panel(api, peer_id):
    """Показать админ-панель."""
    text = (
        " Админ-панель:\n\n"
        "📊 Статистика:\n"
        "  статистика\n\n"
        "👥 Игроки:\n"
        "  игроки\n"
        "  выдать <id> <сумма>\n"
        "  бан <id>\n"
        "  разбан <id>\n\n"
        "🏆 Сезоны:\n"
        "  сбросить сезон\n\n"
        "👹 Босс:\n"
        "  сбросить босса\n\n"
        "📢 Рассылка:\n"
        "  рассылка <текст>"
    )
    send(api, peer_id, text)


def cmd_stats(api, peer_id):
    """Показать статистику бота."""
    stats = db.get_stats()
    text = (
        f"📊 Статистика бота:\n\n"
        f"👥 Всего игроков: {stats['total_players']}\n"
        f"💰 Всего монет: {stats['total_coins']}\n"
        f"⭐ Средний уровень: {stats['avg_level']}\n"
        f"⚔️ Всего дуэлей выиграно: {stats['total_duels']}\n"
        f"👹 Всего боссов убито: {stats['total_boss_kills']}"
    )
    send(api, peer_id, text)


def cmd_players(api, peer_id):
    """Показать список всех игроков."""
    all_players = db.get_all_players()
    if not all_players:
        send(api, peer_id, "Нет игроков.")
        return
    
    lines = [f"👥 Игроки ({len(all_players)}):\n"]
    for i, p in enumerate(all_players[:20], start=1):
        banned = " 🚫" if p["balance"] == -1 else ""
        lines.append(f"{i}. {p['name']}{banned} — ур. {p['level']}, {p['balance']}💰, {p['season_points']}🏆")
    
    if len(all_players) > 20:
        lines.append(f"\n... и ещё {len(all_players) - 20}")
    
    send(api, peer_id, "\n".join(lines))


def cmd_give(api, peer_id, command):
    """Выдать монеты игроку."""
    parts = command.split()
    if len(parts) < 3:
        send(api, peer_id, "Формат: выдать <id> <сумма>")
        return
    
    try:
        target_id = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        send(api, peer_id, "ID и сумма должны быть числами")
        return
    
    if amount <= 0:
        send(api, peer_id, "Сумма должна быть положительной")
        return
    
    if db.add_coins_to_player(target_id, amount):
        target = db.get_player(target_id, lambda uid: get_name(api, uid))
        send(api, peer_id, f"✅ Выдано {amount} монет игроку {target['name']}")
        if target.get("last_peer_id"):
            send(api, target["last_peer_id"], f"🎁 Админ выдал вам {amount} монет!")
    else:
        send(api, peer_id, "Игрок не найден")


def cmd_ban(api, peer_id, command):
    """Забанить игрока."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, "Формат: бан <id>")
        return
    
    try:
        target_id = int(parts[1])
    except ValueError:
        send(api, peer_id, "ID должен быть числом")
        return
    
    if db.ban_player(target_id):
        target = db.get_player(target_id, lambda uid: get_name(api, uid))
        send(api, peer_id, f"🚫 {target['name']} забанен!")
        if target.get("last_peer_id"):
            send(api, target["last_peer_id"], "🚫 Вы были забанены администратором!")
    else:
        send(api, peer_id, "Игрок не найден")


def cmd_unban(api, peer_id, command):
    """Разбанить игрока."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, "Формат: разбан <id>")
        return
    
    try:
        target_id = int(parts[1])
    except ValueError:
        send(api, peer_id, "ID должен быть числом")
        return
    
    if db.unban_player(target_id):
        target = db.get_player(target_id, lambda uid: get_name(api, uid))
        send(api, peer_id, f"✅ {target['name']} разбанен!")
        if target.get("last_peer_id"):
            send(api, target["last_peer_id"], "✅ Вас разбанили! Добро пожаловать обратно!")
    else:
        send(api, peer_id, "Игрок не найден или не забанен")


def cmd_reset_season(api, peer_id):
    """Принудительно сбросить сезон."""
    count = db.force_reset_season()
    send(api, peer_id, f"✅ Сезон сброшен! Награды выданы {count} игрокам.")


def cmd_reset_boss(api, peer_id):
    """Сбросить текущего босса."""
    db.clear_boss()
    send(api, peer_id, "✅ Босс сброшен!")


def cmd_broadcast(api, peer_id, text):
    """Отправить рассылку всем игрокам."""
    message = text[len("рассылка "):].strip()
    if not message:
        send(api, peer_id, "Формат: рассылка <текст сообщения>")
        return
    
    all_players = db.get_all_peer_ids()
    sent_count = 0
    
    for p in all_players:
        try:
            send(api, p["last_peer_id"], f"📢 Важное сообщение от админа:\n\n{message}")
            sent_count += 1
        except Exception as e:
            print(f"Не удалось отправить {p['user_id']}: {e}")
    
    send(api, peer_id, f"✅ Рассылка отправлена {sent_count} игрокам!")