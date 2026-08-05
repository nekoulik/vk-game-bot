"""
Команды кланов: создание, информация, участники, приглашения, кик, выход, роспуск.
"""
import db
from utils.helpers import send, get_name


def cmd_clan_info(api, peer_id, user_id):
    """Показать информацию о клане игрока."""
    clan = db.get_clan(user_id)
    if not clan:
        send(api, peer_id, 
             "🏰 Ты не состоишь в клане.\n\n"
             "Создать: клан создать <название> (5000 монет)\n"
             "Вступить: клан вступить <ID клана>\n"
             "Список кланов: кланы")
        return
    
    members = db.get_clan_members(clan["id"])
    member_count = len(members)
    
    text = (
        f"🏰 {clan['name']}\n\n"
        f"👑 Лидер: {clan['leader_name']}\n"
        f"⭐ Уровень: {clan['level']}\n"
        f"📊 Опыт: {clan['exp']}/{clan['level'] * 100}\n"
        f"💰 Казна: {clan['coins']} монет\n"
        f"👥 Участников: {member_count}\n"
        f"⚔️ Победы: {clan['wins']} | Поражения: {clan['losses']}\n\n"
        f"Твоя роль: {clan['role']}\n\n"
        f"Команды:\n"
        f"  клан участники — список участников\n"
        f"  клан пригласить <id> — пригласить игрока\n"
        f"  клан кикнуть <id> — кикнуть участника\n"
        f"  клан выйти — выйти из клана\n"
        f"  клан распустить — распустить клан (лидер)\n"
        f"  кланы — все кланы"
    )
    send(api, peer_id, text)


def cmd_create(api, peer_id, player, text):
    """Создать новый клан."""
    user_id = player["user_id"]
    clan = db.get_clan(user_id)
    if clan:
        send(api, peer_id, "Ты уже состоишь в клане!")
        return
    
    if player["balance"] < 5000:
        send(api, peer_id, "Недостаточно монет! Создание клана стоит 5000 монет.")
        return
    
    # Извлекаем название из текста команды
    name = text.split(" ", 2)[-1].strip() if " " in text else ""
    if len(name) < 3 or len(name) > 30:
        send(api, peer_id, "Название клана должно быть от 3 до 30 символов.")
        return
    
    clan_id = db.create_clan(name, user_id)
    if not clan_id:
        send(api, peer_id, "Клан с таким названием уже существует!")
        return
    
    player["balance"] -= 5000
    db.save_player(player)
    
    send(api, peer_id, 
         f"🎉 Клан '{name}' создан!\n"
         f"ID клана: {clan_id}\n"
         f"Стоимость: 5000 монет")


def cmd_list(api, peer_id):
    """Показать список всех кланов."""
    clans = db.get_all_clans()
    if not clans:
        send(api, peer_id, "Пока нет кланов. Будь первым!")
        return
    
    lines = ["🏰 Все кланы:\n"]
    for i, c in enumerate(clans[:10], start=1):
        lines.append(f"{i}. {c['name']} (ур. {c['level']}) — {c['member_count']} уч., лидер: {c['leader_name']}")
    
    send(api, peer_id, "\n".join(lines))


def cmd_join(api, peer_id, player, command):
    """Вступить в клан по ID."""
    user_id = player["user_id"]
    clan = db.get_clan(user_id)
    if clan:
        send(api, peer_id, "Ты уже состоишь в клане!")
        return
    
    try:
        clan_id = int(command.split()[-1])
    except (ValueError, IndexError):
        send(api, peer_id, "Формат: клан вступить <ID клана>")
        return
    
    target_clan = db.get_clan_by_id(clan_id)
    if not target_clan:
        send(api, peer_id, "Клан не найден!")
        return
    
    if db.invite_to_clan(clan_id, user_id, user_id):
        send(api, peer_id, f"✅ Ты вступил в клан '{target_clan['name']}'!")
        
        # Уведомить лидера
        leader = db.get_player(target_clan["leader_id"], lambda uid: get_name(api, uid))
        if leader.get("last_peer_id"):
            send(api, leader["last_peer_id"], 
                 f" {player['name']} вступил в клан '{target_clan['name']}'!")
    else:
        send(api, peer_id, "Не удалось вступить в клан.")


def cmd_leave(api, peer_id, user_id):
    """Выйти из клана."""
    clan = db.get_clan(user_id)
    if not clan:
        send(api, peer_id, "Ты не состоишь в клане!")
        return
    
    if clan["role"] == "leader":
        send(api, peer_id, "Лидер не может выйти из клана. Распусти клан: клан распустить")
        return
    
    if db.leave_clan(user_id):
        send(api, peer_id, f"✅ Ты вышел из клана '{clan['name']}'.")
    else:
        send(api, peer_id, "Не удалось выйти из клана.")


def cmd_invite(api, peer_id, user_id, command):
    """Пригласить игрока в клан."""
    clan = db.get_clan(user_id)
    if not clan:
        send(api, peer_id, "Ты не состоишь в клане!")
        return
    
    if clan["role"] not in ["leader", "officer"]:
        send(api, peer_id, "Только лидер и офицеры могут приглашать!")
        return
    
    try:
        target_id = int(command.split()[-1])
    except (ValueError, IndexError):
        send(api, peer_id, "Формат: клан пригласить <ID игрока>")
        return
    
    if target_id == user_id:
        send(api, peer_id, "Нельзя пригласить самого себя!")
        return
    
    if db.invite_to_clan(clan["id"], target_id, user_id):
        target = db.get_player(target_id, lambda uid: get_name(api, uid))
        send(api, peer_id, f"✅ {target['name']} приглашён в клан!")
        
        # Уведомить игрока
        if target.get("last_peer_id"):
            send(api, target["last_peer_id"],
                 f" Тебя пригласили в клан '{clan['name']}'!\n"
                 f"Напиши: клан вступить {clan['id']}")
    else:
        send(api, peer_id, "Игрок уже состоит в клане.")


def cmd_kick(api, peer_id, user_id, command):
    """Кикнуть игрока из клана."""
    clan = db.get_clan(user_id)
    if not clan:
        send(api, peer_id, "Ты не состоишь в клане!")
        return
    
    if clan["role"] not in ["leader", "officer"]:
        send(api, peer_id, "Только лидер и офицеры могут кикать!")
        return
    
    try:
        target_id = int(command.split()[-1])
    except (ValueError, IndexError):
        send(api, peer_id, "Формат: клан кикнуть <ID игрока>")
        return
    
    if db.kick_from_clan(clan["id"], target_id, user_id):
        target = db.get_player(target_id, lambda uid: get_name(api, uid))
        send(api, peer_id, f"✅ {target['name']} кикнут из клана!")
        
        # Уведомить игрока
        if target.get("last_peer_id"):
            send(api, target["last_peer_id"],
                 f"😔 Вас кикнули из клана '{clan['name']}'.")
    else:
        send(api, peer_id, "Не удалось кикнуть игрока.")


def cmd_disband(api, peer_id, user_id):
    """Распустить клан (только для лидера)."""
    clan = db.get_clan(user_id)
    if not clan:
        send(api, peer_id, "Ты не состоишь в клане!")
        return
    
    if clan["role"] != "leader":
        send(api, peer_id, "Только лидер может распустить клан!")
        return
    
    if db.disband_clan(clan["id"], user_id):
        send(api, peer_id, f"🗑️ Клан '{clan['name']}' распущен!")
    else:
        send(api, peer_id, "Не удалось распустить клан.")


def cmd_members(api, peer_id, user_id):
    """Показать список участников клана."""
    clan = db.get_clan(user_id)
    if not clan:
        send(api, peer_id, "Ты не состоишь в клане!")
        return
    
    members = db.get_clan_members(clan["id"])
    lines = [f"👥 Участники клана '{clan['name']}':\n"]
    
    role_emoji = {"leader": "👑", "officer": "⭐", "member": "•"}
    for m in members:
        emoji = role_emoji.get(m["role"], "•")
        lines.append(f"{emoji} {m['name']} (ур. {m['level']}, {m['balance']}💰)")
    
    send(api, peer_id, "\n".join(lines))