"""
Команды уведомлений: настройки, включение/выключение, авто-напоминания.
"""
import datetime
import db
from utils.helpers import send


def cmd_settings(api, peer_id, user_id):
    """Показать текущие настройки уведомлений."""
    settings = db.get_notification_settings(user_id)
    if not settings:
        send(api, peer_id, "❌ Не удалось получить настройки.")
        return
    
    lines = [" Настройки уведомлений:\n"]
    for notif_type, name in db.NOTIFICATION_TYPES.items():
        status = "✅ ВКЛ" if settings.get(notif_type, False) else "❌ ВЫКЛ"
        lines.append(f"{status} {name}")
    
    lines.append("\nУправление:")
    lines.append("  включить <тип> — включить уведомление")
    lines.append("  выключить <тип> — выключить уведомление")
    lines.append("\nТипы: bonus, quests, boss, inactivity")
    send(api, peer_id, "\n".join(lines))


def cmd_enable(api, peer_id, user_id, command):
    """Включить уведомление."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, "Формат: включить <тип>")
        return
    
    notif_type = parts[1].lower()
    if notif_type not in db.NOTIFICATION_TYPES:
        send(api, peer_id, f"Неизвестный тип. Доступные: {', '.join(db.NOTIFICATION_TYPES.keys())}")
        return
    
    db.set_notification_setting(user_id, notif_type, True)
    send(api, peer_id, f"✅ Уведомление '{db.NOTIFICATION_TYPES[notif_type]}' включено!")


def cmd_disable(api, peer_id, user_id, command):
    """Выключить уведомление."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, "Формат: выключить <тип>")
        return
    
    notif_type = parts[1].lower()
    if notif_type not in db.NOTIFICATION_TYPES:
        send(api, peer_id, f"Неизвестный тип. Доступные: {', '.join(db.NOTIFICATION_TYPES.keys())}")
        return
    
    db.set_notification_setting(user_id, notif_type, False)
    send(api, peer_id, f"❌ Уведомление '{db.NOTIFICATION_TYPES[notif_type]}' выключено!")


def check_auto_notifications(api, user_id, peer_id, player):
    """
    Автоматически проверить и отправить напоминания игроку.
    Вызывается из роутера при каждом сообщении.
    """
    notifications = []
    
    # Проверка ежедневного бонуса (если не забрал и прошло 12+ часов)
    today = datetime.date.today().isoformat()
    if player.get("last_bonus") != today:
        if db.should_notify(user_id, "daily_bonus", cooldown_hours=12):
            notifications.append(
                "💰 Не забудь забрать ежедневный бонус!\n"
                "Напиши: бонус"
            )
            db.update_last_notification(user_id, "daily_bonus")
    
    # Проверка невыполненных квестов (если есть и прошло 6+ часов)
    player = db.check_and_reset_daily_quests(player)
    quests_status = db.get_daily_quests_status(player)
    if "⏳" in quests_status and player.get("daily_quest_claimed", 0) == 0:
        if db.should_notify(user_id, "quests", cooldown_hours=6):
            notifications.append(
                "📜 У тебя есть невыполненные квесты!\n"
                "Напиши: квесты"
            )
            db.update_last_notification(user_id, "quests")
    
    # Отправить все накопленные уведомления одним сообщением
    if notifications:
        send(api, peer_id, "🔔 Напоминания:\n\n" + "\n\n".join(notifications))