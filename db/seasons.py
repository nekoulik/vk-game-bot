"""Функции для работы с сезонами."""
from datetime import datetime
from db.base import get_conn
from config.clans import SEASON_REWARDS


def get_current_season():
    """Получить текущий номер сезона (год * 12 + месяц)."""
    now = datetime.now()
    return now.year * 12 + now.month


def get_current_season_number():
    """Получить номер текущего сезона."""
    return get_current_season()


def check_and_reset_season(player):
    """Проверить и сбросить сезон если наступил новый."""
    current_season = get_current_season()
    player_season = player.get("current_season", 1)
    
    if player_season == current_season:
        return player
    
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT COUNT(*) FROM seasons WHERE season_number = ?", (player_season,)
        ).fetchone()[0]
        
        if existing == 0:
            top_players = conn.execute(
                """SELECT user_id, name, season_points, balance 
                   FROM players WHERE season_points > 0
                   ORDER BY season_points DESC LIMIT 3"""
            ).fetchall()
            
            now = datetime.now().isoformat()
            for pos, row in enumerate(top_players, start=1):
                if pos in SEASON_REWARDS:
                    reward = SEASON_REWARDS[pos]
                    conn.execute(
                        "UPDATE players SET balance = balance + ?, title = ? WHERE user_id = ?",
                        (reward["coins"], reward["title"], row["user_id"])
                    )
                    conn.execute(
                        """INSERT INTO seasons 
                           (season_number, user_id, position, season_points, reward_coins, title, ended_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (player_season, row["user_id"], pos, row["season_points"],
                         reward["coins"], reward["title"], now)
                    )
            
            conn.execute("UPDATE players SET season_points = 0")
            conn.execute("UPDATE players SET current_season = ?", (current_season,))
            conn.commit()
    finally:
        conn.close()
    
    player["current_season"] = current_season
    player["season_points"] = 0
    return player


def add_season_points(user_id, points):
    """Добавить сезонные очки игроку."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE players SET season_points = season_points + ? WHERE user_id = ?",
            (points, user_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_season_leaderboard(limit=10):
    """Получить таблицу лидеров сезона."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """SELECT user_id, name, season_points, title, level, balance
               FROM players WHERE season_points > 0
               ORDER BY season_points DESC LIMIT ?""",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_season_history(season_number=None):
    """Получить историю сезонов."""
    conn = get_conn()
    try:
        if season_number:
            rows = conn.execute(
                """SELECT season_number, user_id, position, season_points, reward_coins, title, ended_at
                   FROM seasons WHERE season_number = ?
                   ORDER BY position""",
                (season_number,)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT season_number, user_id, position, season_points, reward_coins, title, ended_at
                   FROM seasons
                   ORDER BY season_number DESC, position"""
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def force_reset_season():
    """Принудительно сбросить сезон."""
    current = get_current_season()
    conn = get_conn()
    try:
        top_players = conn.execute(
            """SELECT user_id, name, season_points, balance 
               FROM players WHERE season_points > 0
               ORDER BY season_points DESC LIMIT 3"""
        ).fetchall()
        
        now = datetime.now().isoformat()
        for pos, row in enumerate(top_players, start=1):
            if pos in SEASON_REWARDS:
                reward = SEASON_REWARDS[pos]
                conn.execute(
                    "UPDATE players SET balance = balance + ?, title = ? WHERE user_id = ?",
                    (reward["coins"], reward["title"], row["user_id"])
                )
                conn.execute(
                    """INSERT INTO seasons 
                       (season_number, user_id, position, season_points, reward_coins, title, ended_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (current, row["user_id"], pos, row["season_points"],
                     reward["coins"], reward["title"], now)
                )
        
        conn.execute("UPDATE players SET season_points = 0")
        conn.execute("UPDATE players SET current_season = ?", (current + 1,))
        conn.commit()
        return len(top_players)
    finally:
        conn.close()