"""
Административные команды: статистика, управление игроками, сбросы, рассылка.
"""
import logging
import time
from datetime import datetime
from vk_api.utils import get_random_id

logger = logging.getLogger('ClubAnicoke')

def is_admin(user_id, admin_ids):
    """Проверка прав администратора"""
    return user_id in admin_ids

def send_admin_error(vk, peer_id):
    """Отправка сообщения об отсутствии прав"""
    vk.messages.send(
        peer_id=peer_id,
        message="❌ У вас нет прав для использования этой команды!",
        random_id=get_random_id()
    )

# ==========================================
# 1. СТАТИСТИКА
# ==========================================
def cmd_stats(vk, peer_id, user_id, username, args, conn, admin_ids, bot):
    """Команда /статистика"""
    if not is_admin(user_id, admin_ids):
        return send_admin_error(vk, peer_id)
    
    try:
        from db.stats import get_server_stats, get_command_stats, get_online_stats
        stats = get_server_stats(conn)
        command_stats = get_command_stats(conn)
        online_stats = get_online_stats(conn)
        
        message = f"""📊 **СТАТИСТИКА СЕРВЕРА**

👥 **Игроки:**
• Всего: {stats['total_players']}
• Активных сегодня: {stats['active_today']}
• Активных за неделю: {stats['active_week']}
• Новых сегодня: {stats['new_players_today']}

💰 **Экономика:**
• Всего монет в игре: {stats['total_money']:,}
• Средний баланс: {int(stats['avg_balance']):,}
• Топ-3 богача:"""
        
        for i, (name, balance) in enumerate(stats['top_rich'], 1):
            message += f"\n  {i}. {name} - {balance:,} 💰"
        
        message += f"""

⚔️ **PvP и дуэли:**
• Всего дуэлей: {stats['total_duels']}
• Активных сейчас: {stats['active_duels']}

👹 **Босс:**
• Уровень: {stats['boss_level']}
• HP: {stats['boss_hp']:,} / {stats['boss_max_hp']:,}
• Атак сегодня: {stats['boss_attacks_today']}

📅 **Обновлено:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"""

        if command_stats:
            message += "\n\n🔥 **Популярные команды (сегодня):**\n"
            for cmd, count in command_stats[:5]:
                message += f"• /{cmd} — {count} раз\n"
        
        vk.messages.send(peer_id=peer_id, message=message, random_id=get_random_id())
    except Exception as e:
        logger.error(f"Ошибка в /статистика: {e}")
        vk.messages.send(peer_id=peer_id, message="⚠️ Ошибка при сборе статистики.", random_id=get_random_id())

# ==========================================
# 2. УПРАВЛЕНИЕ ИГРОКАМИ
# ==========================================
def cmd_give(vk, peer_id, user_id, username, args, conn, admin_ids, bot):
    """Команда /выдать <id> <сумма>"""
    if not is_admin(user_id, admin_ids):
        return send_admin_error(vk, peer_id)
    
    parts = args.split()
    if len(parts) < 2:
        vk.messages.send(peer_id=peer_id, message="❌ Формат: /выдать <id_игрока> <сумма>", random_id=get_random_id())
        return
    
    try:
        target_id = int(parts[0])
        amount = int(parts[1])
    except ValueError:
        vk.messages.send(peer_id=peer_id, message="❌ ID и сумма должны быть числами!", random_id=get_random_id())
        return

    if amount <= 0:
        vk.messages.send(peer_id=peer_id, message="❌ Сумма должна быть больше нуля!", random_id=get_random_id())
        return

    cursor = conn.cursor()
    cursor.execute("UPDATE players SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
    conn.commit()
    
    if cursor.rowcount > 0:
        vk.messages.send(peer_id=peer_id, message=f"✅ Успешно выдано {amount:,} монет игроку с ID {target_id}", random_id=get_random_id())
    else:
        vk.messages.send(peer_id=peer_id, message="❌ Игрок с таким ID не найден в базе.", random_id=get_random_id())

def cmd_ban(vk, peer_id, user_id, username, args, conn, admin_ids, bot):
    """Команда /бан <id>"""
    if not is_admin(user_id, admin_ids):
        return send_admin_error(vk, peer_id)
    
    parts = args.split()
    if not parts:
        vk.messages.send(peer_id=peer_id, message="❌ Формат: /бан <id_игрока>", random_id=get_random_id())
        return
    
    try:
        target_id = int(parts[0])
    except ValueError:
        vk.messages.send(peer_id=peer_id, message="❌ ID должен быть числом!", random_id=get_random_id())
        return

    cursor = conn.cursor()
    # Устанавливаем баланс в -1 как флаг бана (или можно добавить колонку is_banned)
    cursor.execute("UPDATE players SET balance = -1 WHERE user_id = ?", (target_id,))
    conn.commit()
    
    if cursor.rowcount > 0:
        vk.messages.send(peer_id=peer_id, message=f"🚫 Игрок с ID {target_id} успешно забанен!", random_id=get_random_id())
    else:
        vk.messages.send(peer_id=peer_id, message="❌ Игрок не найден.", random_id=get_random_id())

def cmd_unban(vk, peer_id, user_id, username, args, conn, admin_ids, bot):
    """Команда /разбан <id>"""
    if not is_admin(user_id, admin_ids):
        return send_admin_error(vk, peer_id)
    
    try:
        target_id = int(args.split()[0])
    except (ValueError, IndexError):
        vk.messages.send(peer_id=peer_id, message="❌ Формат: /разбан <id_игрока>", random_id=get_random_id())
        return

    cursor = conn.cursor()
    cursor.execute("UPDATE players SET balance = 0 WHERE user_id = ? AND balance = -1", (target_id,))
    conn.commit()
    
    if cursor.rowcount > 0:
        vk.messages.send(peer_id=peer_id, message=f"✅ Игрок с ID {target_id} разбанен!", random_id=get_random_id())
    else:
        vk.messages.send(peer_id=peer_id, message="❌ Игрок не найден или не был забанен.", random_id=get_random_id())

# ==========================================
# 3. УПРАВЛЕНИЕ МИРОМ
# ==========================================
def cmd_reset_boss(vk, peer_id, user_id, username, args, conn, admin_ids, bot):
    """Команда /сброс_босса"""
    if not is_admin(user_id, admin_ids):
        return send_admin_error(vk, peer_id)
    
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE boss_fights 
        SET boss_hp = boss_max_hp, boss_level = boss_level + 1 
        WHERE id = 1
    """)
    conn.commit()
    vk.messages.send(peer_id=peer_id, message="👹 Босс успешно возрождён и стал сильнее! Уровень повышен.", random_id=get_random_id())

def cmd_reset_season(vk, peer_id, user_id, username, args, conn, admin_ids, bot):
    """Команда /сброс_сезона"""
    if not is_admin(user_id, admin_ids):
        return send_admin_error(vk, peer_id)
    
    cursor = conn.cursor()
    # Сбрасываем сезонные очки, но сохраняем общий баланс и уровень
    cursor.execute("UPDATE players SET season_points = 0")
    conn.commit()
    vk.messages.send(peer_id=peer_id, message="🏆 Сезонный рейтинг успешно сброшен для всех игроков!", random_id=get_random_id())

# ==========================================
# 4. РАССЫЛКА
# ==========================================
def cmd_broadcast(vk, peer_id, user_id, username, args, conn, admin_ids, bot):
    """Команда /рассылка <текст>"""
    if not is_admin(user_id, admin_ids):
        return send_admin_error(vk, peer_id)
    
    if not args.strip():
        vk.messages.send(peer_id=peer_id, message="❌ Формат: /рассылка <текст сообщения>", random_id=get_random_id())
        return

    cursor = conn.cursor()
    # Берем только активных (не забаненных) игроков, у которых есть peer_id
    cursor.execute("SELECT user_id, last_peer_id FROM players WHERE balance != -1 AND last_peer_id IS NOT NULL")
    players = cursor.fetchall()
    
    if not players:
        vk.messages.send(peer_id=peer_id, message="⚠️ Нет активных игроков для рассылки.", random_id=get_random_id())
        return

    vk.messages.send(peer_id=peer_id, message=f"⏳ Начинаю рассылку {len(players)} игрокам... Это займёт время.", random_id=get_random_id())
    
    sent_count = 0
    error_count = 0
    
    for player in players:
        try:
            vk.messages.send(
                peer_id=player['last_peer_id'],
                message=f"📢 **Важное сообщение от администрации:**\n\n{args}",
                random_id=get_random_id()
            )
            sent_count += 1
            time.sleep(0.5) # Задержка чтобы VK не заблокировал бота за спам (лимит ~3 сек на 10 сообщений)
        except Exception as e:
            error_count += 1
            logger.warning(f"Не удалось отправить сообщение игроку {player['user_id']}: {e}")
    
    vk.messages.send(
        peer_id=peer_id, 
        message=f"✅ Рассылка завершена!\n📤 Отправлено: {sent_count}\n❌ Ошибок: {error_count}", 
        random_id=get_random_id()
    )

# ==========================================
# 5. РЕГИСТРАЦИЯ КОМАНД
# ==========================================
def register_admin_commands(bot, conn, admin_ids):
    """Регистрация всех админ-команд в боте"""
    
    bot.register_command('статистика', cmd_stats, "Полная статистика сервера")
    bot.register_command('stats', cmd_stats, "Полная статистика сервера")
    
    bot.register_command('выдать', cmd_give, "Выдать монеты: /выдать <id> <сумма>")
    bot.register_command('бан', cmd_ban, "Забанить игрока: /бан <id>")
    bot.register_command('разбан', cmd_unban, "Разбанить игрока: /разбан <id>")
    
    bot.register_command('сброс_босса', cmd_reset_boss, "Возродить и усилить босса")
    bot.register_command('сброс_сезона', cmd_reset_season, "Обнулить сезонный рейтинг всем")
    
    bot.register_command('рассылка', cmd_broadcast, "Отправить сообщение всем: /рассылка <текст>")
    
    logger.info("✅ Административные команды зарегистрированы")