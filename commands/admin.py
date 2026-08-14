"""
Административные команды: статистика, управление игроками, сбросы, рассылка, мут, управление беседой.
"""
import time
from datetime import datetime
from utils.helpers import send, get_name
from utils.keyboard import get_admin_keyboard
import db


def cmd_admin_panel(api, peer_id):
    """Показать админ-панель с кнопками."""
    text = (
        "🛡️ *Админ-панель*\n\n"
        "📊 *Статистика:*\n"
        "  • статистика\n\n"
        "👥 *Игроки:*\n"
        "  • игроки\n"
        "  • выдать <id> <сумма>\n"
        "  • бан <id>\n"
        "  • разбан <id>\n"
        "  • мут <id> <минуты>\n"
        "  • проверить <id>\n"
        "  • очистить <id>\n\n"
        " *Сезоны:*\n"
        "  • сбросить сезон\n\n"
        "👹 *Босс:*\n"
        "  • сбросить босса\n\n"
        "📢 *Рассылка:*\n"
        "  • рассылка <текст>\n\n"
        "💬 *Беседа:*\n"
        "  • ограничить — закрыть беседу\n"
        "  • открыть — открыть беседу\n"
        "  • приветствие <текст>\n"
        "  • прощание <текст>\n"
        "  • настройки беседы\n"
        "  • уведомления <вход/выход> <вкл/выкл>"
    )
    
    keyboard = get_admin_keyboard()
    send(api, peer_id, text, keyboard=keyboard)


def cmd_stats(api, peer_id):
    """Показать статистику бота."""
    stats = db.get_stats()
    text = (
        f" *Статистика бота:*\n\n"
        f"👥 Всего игроков: {stats['total_players']}\n"
        f"💰 Всего монет: {stats['total_coins']:,}\n"
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
        balance = int(p.get("balance", 0))
        if balance == -1:
            status = " "
        elif balance == -2:
            status = " 🔇"
        else:
            status = ""
        lines.append(f"{i}. {p['name']}{status} — ур. {p.get('level', 1)}, {balance}💰, {p.get('season_points', 0)}🏆")
    
    if len(all_players) > 20:
        lines.append(f"\n... и ещё {len(all_players) - 20}")
    
    send(api, peer_id, "\n".join(lines))


def cmd_give(api, peer_id, command):
    """Выдать монеты игроку."""
    parts = command.split()
    if len(parts) < 3:
        send(api, peer_id, "❌ Формат: выдать <id> <сумма>")
        return
    
    try:
        target_id = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        send(api, peer_id, "❌ ID и сумма должны быть числами")
        return
    
    if amount <= 0:
        send(api, peer_id, "❌ Сумма должна быть положительной")
        return
    
    if db.add_coins_to_player(target_id, amount):
        target = db.get_player(target_id, lambda uid: get_name(api, uid))
        send(api, peer_id, f"✅ Выдано {amount} монет игроку {target['name']}")
        if target.get("last_peer_id"):
            send(api, target["last_peer_id"], f" Админ выдал вам {amount} монет!")
    else:
        send(api, peer_id, "❌ Игрок не найден")


def cmd_ban(api, peer_id, command):
    """Забанить игрока."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, " Формат: бан <id>")
        return
    
    try:
        target_id = int(parts[1])
    except ValueError:
        send(api, peer_id, "❌ ID должен быть числом")
        return
    
    if db.ban_player(target_id):
        target = db.get_player(target_id, lambda uid: get_name(api, uid))
        send(api, peer_id, f"🚫 {target['name']} забанен!")
        if target.get("last_peer_id"):
            send(api, target["last_peer_id"], "🚫 Вы были забанены администратором!")
    else:
        send(api, peer_id, "❌ Игрок не найден")


def cmd_unban(api, peer_id, command):
    """Разбанить игрока."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, "❌ Формат: разбан <id>")
        return
    
    try:
        target_id = int(parts[1])
    except ValueError:
        send(api, peer_id, "❌ ID должен быть числом")
        return
    
    if db.unban_player(target_id):
        target = db.get_player(target_id, lambda uid: get_name(api, uid))
        send(api, peer_id, f"✅ {target['name']} разбанен!")
        if target.get("last_peer_id"):
            send(api, target["last_peer_id"], "✅ Вас разбанили! Добро пожаловать обратно!")
    else:
        send(api, peer_id, "❌ Игрок не найден или не забанен")


def cmd_mute(api, peer_id, command):
    """Временный бан (мут) на N минут."""
    parts = command.split()
    if len(parts) < 3:
        send(api, peer_id, "🔇 Формат: мут <id> <минуты>")
        return
    
    try:
        target_id = int(parts[1])
        minutes = int(parts[2])
    except ValueError:
        send(api, peer_id, "❌ ID и минуты должны быть числами!")
        return
    
    if minutes <= 0 or minutes > 1440:
        send(api, peer_id, "❌ Минуты должны быть от 1 до 1440 (24 часа)!")
        return
    
    target = db.get_player(target_id, lambda uid: get_name(api, uid))
    if not target:
        send(api, peer_id, "❌ Игрок не найден!")
        return
    
    target["balance"] = -2
    target["mute_until"] = int(time.time()) + (minutes * 60)
    db.save_player(target)
    
    send(api, peer_id, f"🔇 {target['name']} получил мут на {minutes} минут!")
    
    if target.get("last_peer_id"):
        send(api, target["last_peer_id"], 
             f"🔇 Вы получили мут на {minutes} минут!\n"
             f"Причина: нарушение правил\n"
             f"Размут: через {minutes} минут")


def _format_status(player):
    """Определить статус игрока."""
    balance = int(player.get("balance", 0))
    
    if balance == -1:
        return "🚫 Забанен"
    
    if balance == -2:
        mute_until = player.get("mute_until", 0)
        if mute_until and int(mute_until) > int(time.time()):
            remaining = (int(mute_until) - int(time.time())) // 60
            return f"🔇 Мут ({remaining} мин)"
        else:
            return "✅ Активен (мут истёк)"
    
    return "✅ Активен"


def _format_datetime(dt_value):
    """Форматировать дату из строки или timestamp."""
    if not dt_value:
        return "Неизвестно"
    
    try:
        if isinstance(dt_value, str):
            dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
            return dt.strftime("%d.%m.%Y %H:%M")
        elif isinstance(dt_value, (int, float)):
            return datetime.fromtimestamp(dt_value).strftime("%d.%m.%Y %H:%M")
    except Exception:
        pass
    
    return str(dt_value)


def cmd_check_player(api, peer_id, command):
    """Проверить детальную информацию об игроке."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, " Формат: проверить <id>")
        return
    
    try:
        target_id = int(parts[1])
    except ValueError:
        send(api, peer_id, "❌ ID должен быть числом!")
        return
    
    target = db.get_player(target_id, lambda uid: get_name(api, uid))
    if not target:
        send(api, peer_id, "❌ Игрок не найден!")
        return
    
    status = _format_status(target)
    balance = int(target.get("balance", 0))
    
    text = (
        f" *Информация об игроке:*\n\n"
        f"ID: {target['user_id']}\n"
        f"Имя: {target['name']}\n"
        f"Статус: {status}\n\n"
        f"⭐ Уровень: {target.get('level', 1)}\n"
        f"💰 Баланс: {balance} монет\n"
        f"🏆 Очки сезона: {target.get('season_points', 0)}\n"
        f"💫 Опыт: {target.get('exp', 0)}\n\n"
        f"📅 Регистрация: {_format_datetime(target.get('created_at'))}\n"
        f" Последняя активность: {_format_datetime(target.get('last_activity'))}"
    )
    
    send(api, peer_id, text)


def cmd_clear_player(api, peer_id, command):
    """Сбросить прогресс игрока (баланс, уровень, квесты)."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, "❌ Формат: очистить <id>")
        return
    
    try:
        target_id = int(parts[1])
    except ValueError:
        send(api, peer_id, " ID должен быть числом!")
        return
    
    target = db.get_player(target_id, lambda uid: get_name(api, uid))
    if not target:
        send(api, peer_id, "❌ Игрок не найден!")
        return
    
    target["balance"] = 0
    target["level"] = 1
    target["exp"] = 0
    target["season_points"] = 0
    target["mute_until"] = 0
    db.save_player(target)
    
    send(api, peer_id, f"🗑️ Прогресс игрока {target['name']} сброшен!")
    
    if target.get("last_peer_id"):
        send(api, target["last_peer_id"], 
             "️ Ваш прогресс был сброшен администратором!\n"
             "Начните игру заново с /старт")


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
        send(api, peer_id, "❌ Формат: рассылка <текст сообщения>")
        return
    
    all_players = db.get_all_peer_ids()
    sent_count = 0
    
    for p in all_players:
        try:
            send(api, p["last_peer_id"], f" Важное сообщение от админа:\n\n{message}")
            sent_count += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"Не удалось отправить {p['user_id']}: {e}")
    
    send(api, peer_id, f"✅ Рассылка отправлена {sent_count} игрокам!")


# ==========================================
# УПРАВЛЕНИЕ БЕСЕДОЙ
# ==========================================

def cmd_restrict_chat(api, peer_id, command):
    """Включить ограничение входа в беседу."""
    db.set_chat_restricted(peer_id, 1)
    send(api, peer_id, "🔒 Беседа закрыта! Новые участники будут автоматически выгоняться.")


def cmd_open_chat(api, peer_id, command):
    """Открыть беседу для всех."""
    db.set_chat_restricted(peer_id, 0)
    send(api, peer_id, "🔓 Беседа открыта! Теперь все могут вступать.")


def cmd_set_welcome(api, peer_id, text):
    """Установить приветственное сообщение."""
    message = text[len("приветствие "):].strip()
    if not message:
        send(api, peer_id, "❌ Формат: приветствие <текст>")
        return
    
    db.set_welcome_message(peer_id, message)
    send(api, peer_id, f"✅ Приветственное сообщение установлено:\n{message}")


def cmd_set_goodbye(api, peer_id, text):
    """Установить прощальное сообщение."""
    message = text[len("прощание "):].strip()
    if not message:
        send(api, peer_id, "❌ Формат: прощание <текст>")
        return
    
    db.set_goodbye_message(peer_id, message)
    send(api, peer_id, f"✅ Прощальное сообщение установлено:\n{message}")


def cmd_chat_settings(api, peer_id):
    """Показать настройки беседы."""
    settings = db.get_chat_settings(peer_id)
    
    status = " Закрыта" if settings["is_restricted"] else "🔓 Открыта"
    notify_join = "✅ Вкл" if settings["notify_join"] else "❌ Выкл"
    notify_leave = "✅ Вкл" if settings["notify_leave"] else "❌ Выкл"
    
    text = (
        f"⚙️ *Настройки беседы:*\n\n"
        f"Статус: {status}\n"
        f"Уведомления о входе: {notify_join}\n"
        f"Уведомления о выходе: {notify_leave}\n\n"
        f"Приветствие: {settings['welcome_message'] or 'Не установлено'}\n"
        f"Прощание: {settings['goodbye_message'] or 'Не установлено'}\n\n"
        f"*Команды:*\n"
        f"  • ограничить — закрыть беседу\n"
        f"  • открыть — открыть беседу\n"
        f"  • приветствие <текст> — установить приветствие\n"
        f"  • прощание <текст> — установить прощание\n"
        f"  • уведомления <вход/выход> <вкл/выкл>"
    )
    send(api, peer_id, text)


def cmd_toggle_notify(api, peer_id, command):
    """Переключить уведомления."""
    parts = command.split()
    if len(parts) < 3:
        send(api, peer_id, "❌ Формат: уведомления <вход/выход> <вкл/выкл>")
        return
    
    notify_type = parts[1]
    action = parts[2]
    
    if notify_type not in ["вход", "выход"]:
        send(api, peer_id, "❌ Тип: вход или выход")
        return
    
    if action not in ["вкл", "выкл"]:
        send(api, peer_id, "❌ Действие: вкл или выкл")
        return
    
    enabled = 1 if action == "вкл" else 0
    
    if notify_type == "вход":
        db.set_notify_join(peer_id, enabled)
        send(api, peer_id, f"✅ Уведомления о входе {'включены' if enabled else 'выключены'}")
    else:
        db.set_notify_leave(peer_id, enabled)
        send(api, peer_id, f"✅ Уведомления о выходе {'включены' if enabled else 'выключены'}")

def cmd_update_names(api, peer_id):
    """Обновить имена всех игроков (исправляет старые форматы 'Игрок 123456')."""
    from utils.helpers import get_name
    
    players = db.get_all_players()
    updated_count = 0
    error_count = 0
    
    send(api, peer_id, f"⏳ Начинаю обновление имён... Всего игроков: {len(players)}")
    
    for player in players:
        user_id = player['user_id']
        old_name = player['name']
        
        # Проверяем, нужно ли обновлять имя (старый формат "Игрок 123456789")
        if old_name.startswith('Игрок ') and not old_name.startswith('Игрок #'):
            try:
                new_name = get_name(api, user_id)
                if new_name and new_name != old_name:
                    player['name'] = new_name
                    db.save_player(player)
                    updated_count += 1
                    # Небольшая задержка, чтобы не превысить лимиты VK API (Flood Control)
                    time.sleep(0.1)
            except Exception as e:
                print(f"⚠️ Ошибка обновления имени для {user_id}: {e}")
                error_count += 1
    
    send(api, peer_id, f"✅ Обновление завершено!\n\n📊 Обновлено: {updated_count}\n❌ Ошибок: {error_count}\n👥 Всего проверено: {len(players)}")        
