"""
Роутер команд бота.
Направляет сообщения к соответствующим обработчикам.
"""
from utils.helpers import send
from utils.keyboard import get_main_keyboard, get_admin_keyboard
from commands import basic, admin, boss, quests, games, pvp, clans


def route(command, user_id, peer_id, text, player, api, ADMIN_IDS):
    """
    Распределить команды по обработчикам.
    """
    is_admin = user_id in ADMIN_IDS
    
    # === КНОПКА "НАЗАД" — всегда возвращает в главное меню ===
    if command in ["назад", "back"]:
        keyboard = get_main_keyboard()
        send(api, peer_id, "📋 Главное меню:", keyboard=keyboard)
        return
    
    # === ОСНОВНЫЕ КОМАНДЫ ===
    if command in ["помощь", "help", "хелп", "старт", "start"]:
        return basic.cmd_help(api, peer_id)
    
    if command in ["баланс", "balance"]:
        return basic.cmd_balance(api, peer_id, player)
    
    if command in ["профиль", "profile"]:
        return basic.cmd_profile(api, peer_id, player)
    
    if command in ["топ", "top", "топ игроков", "рейтинг"]:
        return basic.cmd_top(api, peer_id)
    
    if command in ["работа", "work"]:
        return basic.cmd_work(api, peer_id, player)
    
    if command in ["бонус", "bonus", "ежедневный бонус"]:
        return basic.cmd_bonus(api, peer_id, player)
    
    if command.startswith("ставка ") or command == "ставка":
        return basic.cmd_bet(api, peer_id, player, text)
    
    if command in ["дуэль", "duel"]:
        return basic.cmd_duel(api, peer_id, user_id, player, text)
    
    # === МАГАЗИН ===
    if command in ["магазин", "shop"]:
        return basic.cmd_shop(api, peer_id)
    
    if command.startswith("купить ") or command == "купить":
        return basic.cmd_buy(api, peer_id, player, text)
    
    if command in ["инвентарь", "inventory"]:
        return basic.cmd_inventory(api, peer_id, player)
    
    if command.startswith("использовать ") or command == "использовать":
        return basic.cmd_use(api, peer_id, player, text)
    
    if command.startswith("использовать все ") or command == "использовать все":
        return basic.cmd_use_all(api, peer_id, player, text)
    
    if command.startswith("экипировать ") or command == "экипировать":
        return basic.cmd_equip(api, peer_id, player, text)

    # === КВЕСТЫ ===
    if command in ["квесты", "quests"]:
        return quests.cmd_quests(api, peer_id, player)
    
    if command in ["выполнить квесты", "claim quests", "забрать квесты"]:
        return quests.cmd_claim_quests(api, peer_id, player)
    
    # === БОСС ===
    if command in ["босс", "boss"]:
        return boss.cmd_boss(api, peer_id, user_id)
    
    if command in ["создать босса", "spawn boss", "спавн босса"]:
        if is_admin:
            return boss.cmd_spawn_boss(api, peer_id, user_id)
        else:
            send(api, peer_id, "❌ Только админы могут создавать босса!")
            return
    
    if command in ["атака", "атаковать", "attack", "удар"]:
        return boss.cmd_attack_boss(api, peer_id, user_id, player)
    
    # === ИГРЫ ===
    if command in ["игры", "games"]:
        return games.cmd_games_menu(api, peer_id)

    if command.startswith("кнб ") or command == "кнб":
        return games.cmd_rps(api, peer_id, player, text)

    if command.startswith("число ") or command == "число":
        return games.cmd_guess_number(api, peer_id, player, text)

    if command.startswith("рулетка ") or command == "рулетка":
        return games.cmd_roulette(api, peer_id, player, text)

    if command.startswith("монетка ") or command == "монетка":
        return games.cmd_coin(api, peer_id, player, text)
    
    # === PVP-ДУЭЛИ ===
    if command.startswith("вызов ") and len(command.split()) >= 3:
        return pvp.cmd_challenge_pvp(api, peer_id, user_id, player, text)

    if command in ["принять", "accept"]:
        return pvp.cmd_accept_pvp(api, peer_id, user_id, player)

    if command in ["отклонить", "decline"]:
        return pvp.cmd_decline_pvp(api, peer_id, user_id)

    if command in ["бой", "battle", "fight"]:
        return pvp.cmd_pvp_battle(api, peer_id, user_id, player)

    if command in ["pvp", "pvp статус"]:
        return pvp.cmd_pvp_status(api, peer_id, user_id)
    
    if command in ["отменить", "cancel"]:
        return pvp.cmd_cancel_pvp(api, peer_id, user_id)

    # === ДРУГИЕ КОМАНДЫ ===
    if command in ["сезон", "season"]:
        return basic.cmd_season(api, peer_id, user_id, player)
    
    if command in ["клан", "clan"]:
        return clans.cmd_clan(api, peer_id, user_id, player)

    if command.startswith("создать клан"):
        return clans.cmd_create_clan(api, peer_id, user_id, player, text)

    if command in ["клан участники", "clan members"]:
        return clans.cmd_clan_members(api, peer_id, user_id)

    if command.startswith("клан пригласить"):
        return clans.cmd_clan_invite(api, peer_id, user_id, text)

    if command in ["клан выйти", "clan leave"]:
        return clans.cmd_clan_leave(api, peer_id, user_id)

    if command in ["клан топ", "clan top"]:
        return clans.cmd_clan_top(api, peer_id)

    if command in ["клан распустить", "clan disband"]:
        return clans.cmd_clan_disband(api, peer_id, user_id)

    if command in ["клан принять", "clan accept"]:
        return clans.cmd_clan_accept(api, peer_id, user_id, player)

    if command in ["клан найти", "clan find"]:
        return clans.cmd_clan_find(api, peer_id, user_id)

    if command in ["клан казна", "clan treasury"]:
        return clans.cmd_clan_treasury(api, peer_id, user_id)

    if command in ["клан отклонить", "clan decline"]:
        return clans.cmd_clan_decline(api, peer_id, user_id)

    if command.startswith("клан кикнуть"):
        return clans.cmd_clan_kick(api, peer_id, user_id, text)
    
    # === АДМИН-КОМАНДЫ (ТОЛЬКО ДЛЯ АДМИНОВ!) ===
    if is_admin:
        if command in ["админ", "admin", "админка"]:
            return admin.cmd_admin_panel(api, peer_id)
        
        if command in ["статистика", "stats", "stat"]:
            return admin.cmd_stats(api, peer_id)
        
        if command in ["игроки", "players"]:
            return admin.cmd_players(api, peer_id)
        
        if command.startswith("выдать ") or command == "выдать":
            return admin.cmd_give(api, peer_id, text)
        
        if command.startswith("бан ") or command == "бан":
            return admin.cmd_ban(api, peer_id, text)
        
        if command.startswith("разбан ") or command == "разбан":
            return admin.cmd_unban(api, peer_id, text)
        
        if command.startswith("мут ") or command == "мут":
            return admin.cmd_mute(api, peer_id, text)
        
        if command.startswith("проверить ") or command == "проверить":
            return admin.cmd_check_player(api, peer_id, text)
        
        if command.startswith("очистить ") or command == "очистить":
            return admin.cmd_clear_player(api, peer_id, text)
        
        if command in ["сбросить сезон", "reset season"]:
            return admin.cmd_reset_season(api, peer_id)
        
        if command in ["сбросить босса", "reset boss"]:
            return admin.cmd_reset_boss(api, peer_id)
        
        if command.startswith("рассылка ") or command == "рассылка":
            return admin.cmd_broadcast(api, peer_id, text)

        if command in ["обновить имена", "update names"]:
            return admin.cmd_update_names(api, peer_id)
        
        # === УПРАВЛЕНИЕ БЕСЕДОЙ (ТОЛЬКО ДЛЯ АДМИНОВ!) ===
        if command in ["ограничить", "restrict"]:
            return admin.cmd_restrict_chat(api, peer_id, text)
        
        if command in ["открыть", "open"]:
            return admin.cmd_open_chat(api, peer_id, text)
        
        if command.startswith("приветствие ") or command == "приветствие":
            return admin.cmd_set_welcome(api, peer_id, text)
        
        if command.startswith("прощание ") or command == "прощание":
            return admin.cmd_set_goodbye(api, peer_id, text)
        
        if command in ["настройки беседы", "chat settings"]:
            return admin.cmd_chat_settings(api, peer_id)
        
        if command.startswith("уведомления ") or command == "уведомления":
            return admin.cmd_toggle_notify(api, peer_id, text)
    
    # === НЕИЗВЕСТНАЯ КОМАНДА ===
    send(api, peer_id, "❓ Неизвестная команда. Напиши помощь для списка команд.")