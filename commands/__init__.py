"""
Роутер команд.
Распределяет входящие сообщения по нужным модулям.
"""
from commands import basic, shop, pets, boss, quests, seasons, games, notifications, clans, admin
from utils.checks import is_admin, is_banned


def route(command, user_id, peer_id, text, player, api, admin_ids):
    """Направить команду нужному обработчику."""
    
    # Глобальные проверки
    if is_banned(user_id) and not is_admin(user_id, admin_ids):
        from utils.helpers import send
        send(api, peer_id, "🚫 Вы забанены!")
        return
    
    # Уведомления (только для обычных игроков)
    if not is_admin(user_id, admin_ids):
        from commands.notifications import check_auto_notifications
        check_auto_notifications(api, user_id, peer_id, player)

    # === БАЗОВЫЕ КОМАНДЫ ===
    if command in ["старт", "start", "/start", "помощь", "help"]:
        return basic.cmd_start(api, peer_id, player)
    if command in ["баланс", "balance"]:
        return basic.cmd_balance(api, peer_id, player)
    if command in ["id", "айди"]:
        return basic.cmd_id(api, peer_id, user_id)
    if command in ["работа", "work"]:
        return basic.cmd_work(api, peer_id, player)
    if command.startswith("ставка "):
        return basic.cmd_bet(api, peer_id, player, command)
    if command in ["дуэль", "duel"]:
        return basic.cmd_duel(api, peer_id, player)
    if command in ["бонус", "bonus"]:
        return basic.cmd_bonus(api, peer_id, player)
    if command in ["топ", "top"]:
        return basic.cmd_top(api, peer_id)
    if command in ["профиль", "profile"]:
        return basic.cmd_profile(api, peer_id, player)

    # === МАГАЗИН И ИНВЕНТАРЬ ===
    if command in ["магазин", "shop"]:
        return shop.cmd_shop(api, peer_id)
    if command in ["инвентарь", "inv"]:
        return shop.cmd_inventory(api, peer_id, player)
    if command.startswith("купить "):
        return shop.cmd_buy(api, peer_id, player, command)
    if command.startswith("экипировать ") or command.startswith("использовать "):
        return shop.cmd_use(api, peer_id, player, command)

    # === ПИТОМЦЫ ===
    if command in ["питомцы", "pets", "магазин питомцев"]:
        return pets.cmd_pets_shop(api, peer_id, user_id)
    if command in ["мои питомцы", "my pets"]:
        return pets.cmd_my_pets(api, peer_id, user_id)
    if command.startswith("купить питомца "):
        return pets.cmd_buy_pet(api, peer_id, player, command)
    if command.startswith("активировать "):
        return pets.cmd_activate_pet(api, peer_id, user_id, command)

    # === БОСС ===
    if command in ["босс", "boss"]:
        return boss.cmd_start_boss(api, peer_id, user_id)
    if command in ["атака", "attack", "удар"]:
        return boss.cmd_attack_boss(api, peer_id, user_id)
    if command in ["статус", "status"]:
        return boss.cmd_boss_status(api, peer_id, user_id)
    if command in ["сдаться", "leave"]:
        return boss.cmd_leave_boss(api, peer_id, user_id)

    # === КВЕСТЫ ===
    if command in ["квесты", "задания", "quests"]:
        return quests.cmd_quests(api, peer_id, player)
    if command in ["выполнить квесты", "claim quests"]:
        return quests.cmd_claim_quests(api, peer_id, player)
    if command in ["достижения", "achievements"]:
        return quests.cmd_achievements(api, peer_id, user_id)

    # === СЕЗОНЫ ===
    if command in ["сезон", "season", "сезонный рейтинг"]:
        return seasons.cmd_season(api, peer_id, player)
    if command in ["история сезонов", "seasons history"]:
        return seasons.cmd_history(api, peer_id)

    # === МИНИ-ИГРЫ ===
    if command in ["игры", "мини-игры", "games"]:
        return games.cmd_games_menu(api, peer_id)
    if command in ["кнб", "камень ножницы бумага", "rps"]:
        return games.cmd_rps_menu(api, peer_id)
    if command.startswith("кнб ") or command.startswith("rps "):
        return games.cmd_rps_play(api, peer_id, player, command)
    if command in ["угадай", "угадай число", "guess"]:
        return games.cmd_guess_menu(api, peer_id)
    if command.startswith("угадай ") or command.startswith("guess "):
        return games.cmd_guess_play(api, peer_id, player, command)
    if command in ["лотерея", "lottery"]:
        return games.cmd_lottery(api, peer_id, player)

    # === УВЕДОМЛЕНИЯ ===
    if command in ["напоминания", "notifications", "уведомления"]:
        return notifications.cmd_settings(api, peer_id, user_id)
    if command.startswith("включить "):
        return notifications.cmd_enable(api, peer_id, user_id, command)
    if command.startswith("выключить "):
        return notifications.cmd_disable(api, peer_id, user_id, command)

    # === КЛАНЫ ===
    if command in ["клан", "clan"]:
        return clans.cmd_clan_info(api, peer_id, user_id)
    if command.startswith("клан создать ") or command.startswith("clan create "):
        return clans.cmd_create(api, peer_id, player, text)
    if command in ["кланы", "clans"]:
        return clans.cmd_list(api, peer_id)
    if command.startswith("клан вступить ") or command.startswith("clan join "):
        return clans.cmd_join(api, peer_id, player, command)
    if command in ["клан выйти", "clan leave"]:
        return clans.cmd_leave(api, peer_id, user_id)
    if command.startswith("клан пригласить ") or command.startswith("clan invite "):
        return clans.cmd_invite(api, peer_id, user_id, command)
    if command.startswith("клан кикнуть ") or command.startswith("clan kick "):
        return clans.cmd_kick(api, peer_id, user_id, command)
    if command in ["клан распустить", "clan disband"]:
        return clans.cmd_disband(api, peer_id, user_id)
    if command in ["клан участники", "clan members"]:
        return clans.cmd_members(api, peer_id, user_id)

    # === АДМИН ===
    if not is_admin(user_id, admin_ids):
        return  # Неизвестная команда для обычного игрока — молчим
    
    if command in ["админ", "admin"]:
        return admin.cmd_admin_panel(api, peer_id)
    if command in ["статистика", "stats"]:
        return admin.cmd_stats(api, peer_id)
    if command in ["игроки", "players"]:
        return admin.cmd_players(api, peer_id)
    if command.startswith("выдать "):
        return admin.cmd_give(api, peer_id, command)
    if command.startswith("бан "):
        return admin.cmd_ban(api, peer_id, command)
    if command.startswith("разбан "):
        return admin.cmd_unban(api, peer_id, command)
    if command in ["сбросить сезон", "reset season"]:
        return admin.cmd_reset_season(api, peer_id)
    if command in ["сбросить босса", "reset boss"]:
        return admin.cmd_reset_boss(api, peer_id)
    if command.startswith("рассылка "):
        return admin.cmd_broadcast(api, peer_id, text)