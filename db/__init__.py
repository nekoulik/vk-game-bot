"""
Пакет db — слой работы с базой данных.
Все функции импортируются из подмодулей для удобства.
"""

# Базовые функции
from db.base import get_conn, add_column_if_not_exists, init_db

# Игроки
from db.players import (
    migrate_from_json,
    get_player,
    save_player,
    check_and_reset_daily_quests,
    get_all_players,
    add_coins_to_player,
    ban_player,
    unban_player,
    is_player_banned,
    get_stats,
    get_top_players,
    update_daily_progress,
    get_all_peer_ids,
)

# Предметы и инвентарь
from db.items import (
    get_inventory,
    add_to_inventory,
    remove_from_inventory,
    get_equipment,
    set_equipment,
)

# Питомцы
from db.pets import (
    get_player_pets,
    buy_pet,
    activate_pet,
    get_active_pet,
    get_pet_bonus,
)

# Босс
from db.boss import (
    get_boss,
    save_boss,
    clear_boss,
)

# Дуэли
from db.duels import (
    get_duel,
    save_duel,
    delete_duel,
    create_duel_challenge,
    get_duel_challenge_for_user,
    get_duel_challenges_for_user,
    clear_duel_challenge,
    start_duel,
    get_active_duel,
    end_duel,
)

# Квесты и достижения
from db.quests import (
    claim_daily_quests,
    get_daily_quests_status,
    unlock_achievement,
    get_achievements_list,
    check_achievements_on_action,
)

# Сезоны
from db.seasons import (
    get_current_season,
    get_current_season_number,
    check_and_reset_season,
    add_season_points,
    get_season_leaderboard,
    get_season_history,
    force_reset_season,
)

# Кланы
from db.clans import (
    create_clan,
    get_clan,
    get_clan_by_id,
    get_clan_members,
    invite_to_clan,
    leave_clan,
    kick_from_clan,
    disband_clan,
    get_all_clans,
    add_clan_exp,
    get_clan_bonus,
    start_clan_war,
    end_clan_war,
)

# Уведомления
from db.notifications import (
    NOTIFICATION_TYPES,
    get_notification_settings,
    set_notification_setting,
    get_last_notification_time,
    update_last_notification,
    should_notify,
    get_inactive_players,
)


# Автоматическая инициализация при импорте
init_db()
migrate_from_json()