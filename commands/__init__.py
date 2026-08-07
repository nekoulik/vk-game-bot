"""
Роутер команд — распределяет сообщения по обработчикам.
"""
from commands import basic, shop, pets, boss, quests, seasons, games, notifications, clans, admin


def route(command, user_id, peer_id, text, player, api, ADMIN_IDS):
    """
    Распределить команду по обработчикам.
    
    Args:
        command: Текст команды (нижний регистр)
        user_id: ID пользователя
        peer_id: ID чата
        text: Оригинальный текст
        player: Данные игрока
        api: VK API
        ADMIN_IDS: Список ID админов
    """
    # Основные команды
    if command in ["старт", "start", "помощь", "help"]:
        return basic.cmd_help(api, peer_id)
    
    if command in ["баланс", "balance"]:
        return basic.cmd_balance(api, peer_id, player)
    
    if command in ["профиль", "profile"]:
        return basic.cmd_profile(api, peer_id, player)
    
    if command in ["топ", "top"]:
        return basic.cmd_top(api, peer_id)
    
    if command in ["работа", "work"]:
        return basic.cmd_work(api, peer_id, player)
    
    if command in ["бонус", "bonus"]:
        return basic.cmd_bonus(api, peer_id, player)

    if command.startswith("ставка 50") or command.startswith("bet "):
        return basic.cmd_bet(api, peer_id, player, command)

    # PvP дуэли
    if command.startswith("вызов "):
        return basic.cmd_challenge(api, peer_id, user_id, command)
    
    if command in ["принять", "accept"]:
        return basic.cmd_accept_duel(api, peer_id, user_id, player)
    
    if command in ["отклонить", "decline"]:
        return basic.cmd_decline_duel(api, peer_id, user_id)
    
    if command in ["дуэль", "duel"]:
        return basic.cmd_duel(api, peer_id, user_id, player, command)
    
    if command.startswith("дуэль ") or command.startswith("duel "):
        return basic.cmd_duel(api, peer_id, user_id, player, command)

    if command in ["статус дуэли", "duel status"]:
        return basic.cmd_duel_status(api, peer_id, user_id)
        
    # Питомцы (ПЕРЕД магазином, чтобы "купить питомца" не перехватывался shop)
    if command in ["питомцы", "pets", "мои питомцы", "my pets"]:
        return pets.cmd_pets_shop(api, peer_id, user_id)
    
    if command.startswith("купить питомца "):
        return pets.cmd_buy_pet(api, peer_id, player, command)
    
    if command.startswith("активировать "):
        return pets.cmd_activate_pet(api, peer_id, user_id, command)
    
    # Магазин (ПОСЛЕ питомцев)
    if command in ["магазин", "shop", "store"]:
        return shop.cmd_shop(api, peer_id)
    
    if command in ["инвентарь", "inventory", "инв"]:
        return shop.cmd_inventory(api, peer_id, player)
    
    if command.startswith("купить ") or command.startswith("buy "):
        return shop.cmd_buy(api, peer_id, player, command)
    
    if command.startswith("экипировать ") or command.startswith("equip "):
        return shop.cmd_use(api, peer_id, player, command)
    
    # Босс
    if command in ["босс", "boss"]:
        return boss.cmd_start_boss(api, peer_id, user_id)
    
    if command in ["атака", "attack"]:
        return boss.cmd_attack_boss(api, peer_id, user_id)
    
    if command in ["статус", "boss status"]:
        return boss.cmd_boss_status(api, peer_id, user_id)
    
    if command in ["сдаться", "give up"]:
        return boss.cmd_leave_boss(api, peer_id, user_id)
    
    # Квесты
    if command in ["квесты", "quests"]:
        return quests.cmd_quests(api, peer_id, player)
    
    if command in ["выполнить квесты", "claim quests"]:
        return quests.cmd_claim_quests(api, peer_id, player)
    
    if command in ["достижения", "achievements"]:
        return quests.cmd_achievements(api, peer_id, user_id)
    
    # Сезоны
    if command in ["сезон", "season"]:
        return seasons.cmd_season(api, peer_id, player)
    
    if command in ["история сезонов", "season history"]:
        return seasons.cmd_history(api, peer_id)
    
    # Мини-игры
    if command in ["игры", "games"]:
        return games.cmd_games_menu(api, peer_id)
    
    if command in ["кнб", "rps"]:
        return games.cmd_rps_menu(api, peer_id)
    
    if command.startswith("кнб ") or command.startswith("rps "):
        return games.cmd_rps_play(api, peer_id, player, command)
    
    if command in ["угадай", "guess"]:
        return games.cmd_guess_menu(api, peer_id)
    
    if command.startswith("угадай ") or command.startswith("guess "):
        return games.cmd_guess_play(api, peer_id, player, command)
    
    if command in ["лотерея", "lottery"]:
        return games.cmd_lottery(api, peer_id, player)
    
    # Кланы
    if command in ["клан", "clan"]:
        return clans.cmd_clan_info(api, peer_id, user_id)
    
    if command.startswith("клан создать "):
        return clans.cmd_create(api, peer_id, player, text)
    
    if command in ["кланы", "clans"]:
        return clans.cmd_list(api, peer_id)
    
    if command.startswith("клан вступить "):
        return clans.cmd_join(api, peer_id, player, command)
    
    if command in ["клан выйти", "clan leave"]:
        return clans.cmd_leave(api, peer_id, user_id)
    
    if command.startswith("клан пригласить "):
        return clans.cmd_invite(api, peer_id, user_id, command)
    
    if command.startswith("клан кикнуть "):
        return clans.cmd_kick(api, peer_id, user_id, command)
    
    if command in ["клан распустить", "clan disband"]:
        return clans.cmd_disband(api, peer_id, user_id)
    
    if command in ["клан участники", "clan members"]:
        return clans.cmd_members(api, peer_id, user_id)
    
    # Настройки (объединили напоминания и настройки)
    if command in ["настройки", "settings", "напоминания", "notifications", "уведомления"]:
        return notifications.cmd_settings(api, peer_id, user_id)

    if command.startswith("включить "):
        return notifications.cmd_enable(api, peer_id, user_id, command)

    if command.startswith("выключить "):
        return notifications.cmd_disable(api, peer_id, user_id, command)
    
    # Админ-команды
    if user_id in ADMIN_IDS:
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