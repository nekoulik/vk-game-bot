"""Функции для работы с кланами."""
from datetime import datetime
from db.base import get_conn
from config.clans import CLAN_BONUSES


def init_clans_table():
    """Инициализировать таблицы кланов."""
    conn = get_conn()
    try:
        # Таблица кланов
        conn.execute('''
            CREATE TABLE IF NOT EXISTS clans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                leader_id INTEGER,
                exp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (leader_id) REFERENCES players(user_id)
            )
        ''')
        
        # Таблица участников клана
        conn.execute('''
            CREATE TABLE IF NOT EXISTS clan_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan_id INTEGER,
                user_id INTEGER,
                role TEXT DEFAULT 'member',
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id),
                FOREIGN KEY (clan_id) REFERENCES clans(id),
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        # Таблица клановых войн
        conn.execute('''
            CREATE TABLE IF NOT EXISTS clan_wars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan1_id INTEGER,
                clan2_id INTEGER,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_time DATETIME,
                winner_id INTEGER,
                clan1_score INTEGER DEFAULT 0,
                clan2_score INTEGER DEFAULT 0,
                FOREIGN KEY (clan1_id) REFERENCES clans(id),
                FOREIGN KEY (clan2_id) REFERENCES clans(id)
            )
        ''')
        
        conn.commit()
        print("✅ Таблицы кланов созданы")
    finally:
        conn.close()


def create_clan(name, leader_id):
    """Создать клан."""
    conn = get_conn()
    try:
        now = datetime.now().isoformat()
        cursor = conn.execute(
            "INSERT INTO clans (name, leader_id, created_at) VALUES (?, ?, ?)",
            (name, leader_id, now)
        )
        clan_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO clan_members (clan_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
            (clan_id, leader_id, 'leader', now)
        )
        conn.commit()
        return clan_id
    except Exception:
        return None
    finally:
        conn.close()


def get_clan(user_id):
    """Получить клан игрока (только если он уже принял приглашение)."""
    conn = get_conn()
    try:
        # ✅ ВАЖНО: исключаем роль 'invited' — это только приглашение, не членство
        row = conn.execute(
            """SELECT c.*, cm.role, p.name as leader_name
               FROM clan_members cm
               JOIN clans c ON cm.clan_id = c.id
               JOIN players p ON c.leader_id = p.user_id
               WHERE cm.user_id = ? AND cm.role != 'invited'""",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_pending_invite(user_id):
    """Получить активное приглашение игрока (роль 'invited')."""
    conn = get_conn()
    try:
        row = conn.execute(
            """SELECT cm.*, c.name as clan_name
               FROM clan_members cm
               JOIN clans c ON cm.clan_id = c.id
               WHERE cm.user_id = ? AND cm.role = 'invited'""",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_clan_by_id(clan_id):
    """Получить клан по ID."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM clans WHERE id = ?", (clan_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_clan_members(clan_id):
    """Получить всех участников клана (без приглашённых)."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """SELECT cm.*, p.name, p.balance, p.level 
               FROM clan_members cm
               JOIN players p ON cm.user_id = p.user_id
               WHERE cm.clan_id = ? AND cm.role != 'invited'
               ORDER BY 
                 CASE cm.role 
                   WHEN 'leader' THEN 1 
                   WHEN 'officer' THEN 2 
                   ELSE 3 
                 END,
               p.level DESC""",
            (clan_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def invite_to_clan(clan_id, user_id, inviter_id):
    """Пригласить игрока в клан (создаёт запись со статусом 'invited')."""
    conn = get_conn()
    try:
        # Проверяем, не состоит ли уже в клане (любая роль кроме invited)
        existing = conn.execute(
            "SELECT 1 FROM clan_members WHERE user_id = ? AND role != 'invited'",
            (user_id,)
        ).fetchone()
        if existing:
            return False
        
        # Проверяем, нет ли уже активного приглашения
        existing_invite = conn.execute(
            "SELECT 1 FROM clan_members WHERE user_id = ? AND role = 'invited'",
            (user_id,)
        ).fetchone()
        
        now = datetime.now().isoformat()
        
        if existing_invite:
            # Обновляем старое приглашение на новое
            conn.execute(
                "UPDATE clan_members SET clan_id = ?, joined_at = ? WHERE user_id = ? AND role = 'invited'",
                (clan_id, now, user_id)
            )
        else:
            # Создаём новое приглашение
            conn.execute(
                "INSERT INTO clan_members (clan_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
                (clan_id, user_id, 'invited', now)
            )
        
        conn.commit()
        return True
    finally:
        conn.close()


def accept_clan_invite(user_id):
    """Принять приглашение в клан (меняет роль с 'invited' на 'member')."""
    conn = get_conn()
    try:
        invite = conn.execute(
            """SELECT cm.*, c.name as clan_name
               FROM clan_members cm
               JOIN clans c ON cm.clan_id = c.id
               WHERE cm.user_id = ? AND cm.role = 'invited'""",
            (user_id,)
        ).fetchone()
        
        if not invite:
            return None
        
        invite = dict(invite)
        
        # Меняем роль на 'member'
        conn.execute(
            "UPDATE clan_members SET role = 'member', joined_at = ? WHERE user_id = ? AND role = 'invited'",
            (datetime.now().isoformat(), user_id)
        )
        conn.commit()
        
        return invite
    finally:
        conn.close()


def decline_clan_invite(user_id):
    """Отклонить приглашение в клан (удаляет запись)."""
    conn = get_conn()
    try:
        conn.execute(
            "DELETE FROM clan_members WHERE user_id = ? AND role = 'invited'",
            (user_id,)
        )
        conn.commit()
    finally:
        conn.close()


def leave_clan(user_id):
    """Выйти из клана."""
    conn = get_conn()
    try:
        clan = get_clan(user_id)
        if not clan:
            return False
        
        if clan["role"] == "leader":
            return False
        
        conn.execute(
            "DELETE FROM clan_members WHERE user_id = ?", (user_id,)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def kick_from_clan(clan_id, user_id, kicker_id):
    """Кикнуть игрока из клана."""
    conn = get_conn()
    try:
        kicker_clan = get_clan(kicker_id)
        if not kicker_clan or kicker_clan["id"] != clan_id:
            return False
        
        if kicker_clan["role"] not in ["leader", "officer"]:
            return False
        
        target = conn.execute(
            "SELECT role FROM clan_members WHERE clan_id = ? AND user_id = ?",
            (clan_id, user_id)
        ).fetchone()
        
        if not target or target["role"] == "leader":
            return False
        
        conn.execute(
            "DELETE FROM clan_members WHERE clan_id = ? AND user_id = ?",
            (clan_id, user_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def disband_clan(clan_id, leader_id):
    """Распустить клан."""
    conn = get_conn()
    try:
        clan = get_clan_by_id(clan_id)
        if not clan or clan["leader_id"] != leader_id:
            return False
        
        conn.execute("DELETE FROM clan_members WHERE clan_id = ?", (clan_id,))
        conn.execute("DELETE FROM clans WHERE id = ?", (clan_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def get_all_clans():
    """Получить все кланы."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """SELECT c.*, p.name as leader_name,
                  (SELECT COUNT(*) FROM clan_members WHERE clan_id = c.id AND role != 'invited') as member_count
               FROM clans c
               JOIN players p ON c.leader_id = p.user_id
               ORDER BY c.level DESC, c.exp DESC"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_clan_exp(clan_id, amount):
    """Добавить опыт клану."""
    conn = get_conn()
    try:
        clan = get_clan_by_id(clan_id)
        if not clan:
            return
        
        new_exp = clan["exp"] + amount
        new_level = clan["level"]
        
        while new_exp >= new_level * 100:
            new_exp -= new_level * 100
            new_level += 1
        
        conn.execute(
            "UPDATE clans SET exp = ?, level = ? WHERE id = ?",
            (new_exp, new_level, clan_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_clan_bonus(clan_id, bonus_type):
    """Получить бонус клана."""
    clan = get_clan_by_id(clan_id)
    if not clan:
        return 0.0
    
    level = min(clan["level"], 5)
    return CLAN_BONUSES[level].get(bonus_type, 0.0)


def start_clan_war(clan1_id, clan2_id):
    """Начать клановую войну."""
    conn = get_conn()
    try:
        now = datetime.now().isoformat()
        cursor = conn.execute(
            """INSERT INTO clan_wars (clan1_id, clan2_id, start_time) 
               VALUES (?, ?, ?)""",
            (clan1_id, clan2_id, now)
        )
        return cursor.lastrowid
    finally:
        conn.close()


def end_clan_war(war_id, winner_id, clan1_score, clan2_score):
    """Завершить клановую войну."""
    conn = get_conn()
    try:
        now = datetime.now().isoformat()
        war = conn.execute(
            "SELECT * FROM clan_wars WHERE id = ?", (war_id,)
        ).fetchone()
        
        if not war:
            return False
        
        conn.execute(
            """UPDATE clan_wars 
               SET end_time = ?, winner_id = ?, clan1_score = ?, clan2_score = ?
               WHERE id = ?""",
            (now, winner_id, clan1_score, clan2_score, war_id)
        )
        
        if winner_id == war["clan1_id"]:
            conn.execute("UPDATE clans SET wins = wins + 1 WHERE id = ?", (war["clan1_id"],))
            conn.execute("UPDATE clans SET losses = losses + 1 WHERE id = ?", (war["clan2_id"],))
        elif winner_id == war["clan2_id"]:
            conn.execute("UPDATE clans SET wins = wins + 1 WHERE id = ?", (war["clan2_id"],))
            conn.execute("UPDATE clans SET losses = losses + 1 WHERE id = ?", (war["clan1_id"],))
        
        conn.commit()
        return True
    finally:
        conn.close()