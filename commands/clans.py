"""
Команды для управления кланами.
"""
from datetime import datetime
from utils.helpers import send, format_number, get_name
import db


def cmd_clan(api, peer_id, user_id, player):
    """Показать информацию о клане игрока."""
    clan = db.clans.get_clan(user_id)
    
    if not clan:
        # Проверяем, есть ли активное приглашение
        invite = db.clans.get_pending_invite(user_id)
        if invite:
            text = (
                f"🛡️ *У тебя нет клана, но есть приглашение!*\n\n"
                f"📨 Тебя пригласили в клан *{invite['clan_name']}*\n"
                f"Напиши *клан принять* чтобы вступить\n"
                f"или *клан отклонить* чтобы отказаться.\n\n"
                f"📋 *Другие команды:*\n"
                f"  • создать клан <название> — создать свой клан (1000 монет)\n"
                f"  • клан топ — список лучших кланов\n"
                f"  • клан найти — найти клан для вступления"
            )
        else:
            text = (
                "🛡️ *У тебя нет клана!*\n\n"
                "📋 *Команды:*\n"
                "  • создать клан <название> — создать свой клан (1000 монет)\n"
                "  • клан топ — список лучших кланов\n"
                "  • клан найти — найти клан для вступления"
            )
        send(api, peer_id, text)
        return
    
    members = db.clans.get_clan_members(clan["id"])
    member_count = len(members)
    
    # Бонусы клана
    from config.clans import CLAN_BONUSES
    level = min(clan["level"], 5)
    bonuses = CLAN_BONUSES.get(level, {})
    
    text = (
        f"🛡️ *Клан: {clan['name']}*\n\n"
        f" Лидер: {clan['leader_name']}\n"
        f"⭐ Уровень: {clan['level']}\n"
        f"💫 Опыт: {clan['exp']}/{clan['level'] * 100}\n"
        f"👥 Участников: {member_count}\n"
        f"🏆 Побед: {clan.get('wins', 0)} | Поражений: {clan.get('losses', 0)}\n\n"
        f" *Активные бонусы:*\n"
        f"  • К монетам: +{int(bonuses.get('coins', 0) * 100)}%\n"
        f"  • К урону: +{int(bonuses.get('damage', 0) * 100)}%\n"
        f"  • К опыту: +{int(bonuses.get('exp', 0) * 100)}%\n\n"
        f"📋 *Команды:*\n"
        f"  • клан участники — список участников\n"
        f"  • клан пригласить <id> — пригласить игрока\n"
        f"  • клан кикнуть <id> — исключить игрока\n"
        f"  • клан выйти — покинуть клан\n"
        f"  • клан распустить — распустить клан (лидер)\n"
        f"  • клан казна — информация о казне"
    )
    send(api, peer_id, text)


def cmd_create_clan(api, peer_id, user_id, player, command):
    """Создать клан."""
    # Проверяем, есть ли уже клан
    existing_clan = db.clans.get_clan(user_id)
    if existing_clan:
        send(api, peer_id, "❌ Ты уже состоишь в клане!")
        return
    
    # Проверяем, нет ли активного приглашения
    invite = db.clans.get_pending_invite(user_id)
    if invite:
        send(api, peer_id, f"❌ У тебя есть активное приглашение в клан *{invite['clan_name']}*! Напиши *клан принять* или *клан отклонить*.")
        return
    
    # Парсим название
    parts = command.split(maxsplit=1)
    if len(parts) < 2:
        send(api, peer_id, "❌ Формат: создать клан <название>")
        return
    
    clan_name = parts[1].strip()
    if len(clan_name) < 3 or len(clan_name) > 30:
        send(api, peer_id, "❌ Название должно быть от 3 до 30 символов!")
        return
    
    # Проверяем баланс
    cost = 1000
    balance = int(player.get("balance", 0))
    if balance < cost:
        send(api, peer_id, f"❌ Недостаточно монет! Нужно {cost}, у тебя {balance}")
        return
    
    # Создаём клан
    clan_id = db.clans.create_clan(clan_name, user_id)
    
    if not clan_id:
        send(api, peer_id, "❌ Клан с таким названием уже существует!")
        return
    
    # Снимаем деньги
    player["balance"] = balance - cost
    db.save_player(player)
    
    send(api, peer_id, f"✅ Клан *{clan_name}* успешно создан!\n💰 Списано {cost} монет.\n\nТеперь ты лидер клана!")


def cmd_clan_members(api, peer_id, user_id):
    """Показать участников клана."""
    clan = db.clans.get_clan(user_id)
    if not clan:
        send(api, peer_id, "❌ Ты не состоишь в клане!")
        return
    
    members = db.clans.get_clan_members(clan["id"])
    
    lines = [f"👥 *Участники клана {clan['name']}:*\n\n"]
    
    for i, member in enumerate(members, start=1):
        role_emoji = "👑" if member["role"] == "leader" else "🔷" if member["role"] == "officer" else "•"
        lines.append(f"{i}. {role_emoji} {member['name']} (ур. {member.get('level', 1)})")
    
    send(api, peer_id, "\n".join(lines))


def cmd_clan_invite(api, peer_id, user_id, command):
    """Пригласить игрока в клан."""
    clan = db.clans.get_clan(user_id)
    if not clan:
        send(api, peer_id, "❌ Ты не состоишь в клане!")
        return
    
    # Проверяем права
    if clan["role"] not in ["leader", "officer"]:
        send(api, peer_id, "❌ Только лидер и офицеры могут приглашать!")
        return
    
    parts = command.split()
    if len(parts) < 3:
        send(api, peer_id, "❌ Формат: клан пригласить <id>")
        return
    
    try:
        target_id = int(parts[2])
    except ValueError:
        send(api, peer_id, "❌ ID должен быть числом!")
        return
    
    if target_id == user_id:
        send(api, peer_id, "❌ Нельзя пригласить себя!")
        return
    
    # Проверяем, не состоит ли уже в клане
    target_clan = db.clans.get_clan(target_id)
    if target_clan:
        send(api, peer_id, "❌ Этот игрок уже состоит в клане!")
        return
    
    # Приглашаем
    success = db.clans.invite_to_clan(clan["id"], target_id, user_id)
    
    if success:
        target_name = get_name(api, target_id)
        send(api, peer_id, f"✅ {target_name} приглашён в клан!")
        
        # Уведомляем игрока напрямую
        try:
            send(
                api, target_id,
                f"🛡️ Тебя пригласили в клан *{clan['name']}*!\n"
                f"Напиши *клан принять* чтобы вступить\n"
                f"или *клан отклонить* чтобы отказаться."
            )
        except Exception as e:
            print(f"⚠️ Не удалось уведомить {target_id}: {e}")
    else:
        send(api, peer_id, " Не удалось пригласить игрока! Возможно, у него уже есть активное приглашение.")


def cmd_clan_accept(api, peer_id, user_id, player):
    """Принять приглашение в клан."""
    invite = db.clans.accept_clan_invite(user_id)
    
    if not invite:
        send(api, peer_id, "❌ У тебя нет активных приглашений!")
        return
    
    clan_name = invite["clan_name"]
    send(api, peer_id, f"✅ Ты вступил в клан *{clan_name}*!\n\nНапиши *клан* чтобы посмотреть информацию.")


def cmd_clan_decline(api, peer_id, user_id):
    """Отклонить приглашение в клан."""
    invite = db.clans.get_pending_invite(user_id)
    
    if not invite:
        send(api, peer_id, "❌ У тебя нет активных приглашений!")
        return
    
    clan_name = invite["clan_name"]
    db.clans.decline_clan_invite(user_id)
    send(api, peer_id, f"❌ Ты отклонил приглашение в клан *{clan_name}*.")


def cmd_clan_kick(api, peer_id, user_id, command):
    """Кикнуть игрока из клана."""
    clan = db.clans.get_clan(user_id)
    if not clan:
        send(api, peer_id, "❌ Ты не состоишь в клане!")
        return
    
    if clan["role"] not in ["leader", "officer"]:
        send(api, peer_id, "❌ Только лидер и офицеры могут исключать!")
        return
    
    parts = command.split()
    if len(parts) < 3:
        send(api, peer_id, " Формат: клан кикнуть <id>")
        return
    
    try:
        target_id = int(parts[2])
    except ValueError:
        send(api, peer_id, "❌ ID должен быть числом!")
        return
    
    if target_id == user_id:
        send(api, peer_id, "❌ Нельзя исключить себя! Используй *клан выйти*.")
        return
    
    success = db.clans.kick_from_clan(clan["id"], target_id, user_id)
    
    if success:
        target_name = get_name(api, target_id)
        send(api, peer_id, f"✅ {target_name} исключён из клана!")
    else:
        send(api, peer_id, "❌ Не удалось исключить игрока! Возможно, он не состоит в клане или является лидером.")


def cmd_clan_leave(api, peer_id, user_id):
    """Выйти из клана."""
    clan = db.clans.get_clan(user_id)
    if not clan:
        send(api, peer_id, "❌ Ты не состоишь в клане!")
        return
    
    if clan["role"] == "leader":
        send(api, peer_id, "❌ Лидер не может выйти из клана! Распусти клан (*клан распустить*) или передай лидерство.")
        return
    
    success = db.clans.leave_clan(user_id)
    
    if success:
        send(api, peer_id, f"✅ Ты покинул клан *{clan['name']}*!")
    else:
        send(api, peer_id, "❌ Не удалось выйти из клана!")


def cmd_clan_top(api, peer_id):
    """Показать топ кланов."""
    clans = db.clans.get_all_clans()
    
    if not clans:
        send(api, peer_id, "🛡️ Пока нет ни одного клана!")
        return
    
    lines = ["🏆 *Топ кланов:*\n\n"]
    
    for i, clan in enumerate(clans[:10], start=1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        lines.append(f"{medal} {clan['name']} (ур. {clan['level']}) — {clan['member_count']} уч.")
    
    send(api, peer_id, "\n".join(lines))


def cmd_clan_disband(api, peer_id, user_id):
    """Распустить клан (только лидер)."""
    clan = db.clans.get_clan(user_id)
    if not clan:
        send(api, peer_id, "❌ Ты не состоишь в клане!")
        return
    
    if clan["role"] != "leader":
        send(api, peer_id, "❌ Только лидер может распустить клан!")
        return
    
    success = db.clans.disband_clan(clan["id"], user_id)
    
    if success:
        send(api, peer_id, f"✅ Клан *{clan['name']}* распущен!")
    else:
        send(api, peer_id, "❌ Не удалось распустить клан!")


def cmd_clan_find(api, peer_id, user_id):
    """Показать список кланов для вступления."""
    # Проверяем, состоит ли игрок в клане
    user_clan = db.clans.get_clan(user_id)
    if user_clan:
        send(api, peer_id, f"❌ Ты уже состоишь в клане *{user_clan['name']}*!")
        return
    
    clans = db.clans.get_all_clans()
    
    if not clans:
        send(api, peer_id, "🛡️ Пока нет ни одного клана!")
        return
    
    lines = ["🔍 *Кланы для вступления:*\n\n"]
    
    for i, clan in enumerate(clans[:10], start=1):
        lines.append(f"{i}. 🛡️ {clan['name']} (ур. {clan['level']}) — {clan['member_count']} уч.\n    👑 Лидер: {clan['leader_name']}")
    
    lines.append("\n💡 Чтобы вступить, попроси лидера или офицера клана пригласить тебя.\n Команда: *клан пригласить <твой id>*")
    
    send(api, peer_id, "\n".join(lines))


def cmd_clan_treasury(api, peer_id, user_id):
    """Показать казну клана."""
    clan = db.clans.get_clan(user_id)
    if not clan:
        send(api, peer_id, "❌ Ты не состоишь в клане!")
        return
    
    members = db.clans.get_clan_members(clan["id"])
    member_count = len(members)
    
    text = (
        f"💰 *Казна клана {clan['name']}:*\n\n"
        f"⭐ Уровень: {clan['level']}\n"
        f"💫 Опыт: {clan['exp']}/{clan['level'] * 100}\n"
        f"👥 Участников: {member_count}\n"
        f"🏆 Побед: {clan.get('wins', 0)}\n"
        f"💔 Поражений: {clan.get('losses', 0)}\n\n"
        f"📊 Чем больше опыта — тем выше уровень и бонусы!\n"
        f"💡 Опыт начисляется за победы в дуэлях и убийства боссов."
    )
    send(api, peer_id, text)