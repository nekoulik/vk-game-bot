"""
Команды сезонов: текущий рейтинг и история сезонов.
"""
import db
from utils.helpers import send, get_name


def cmd_season(api, peer_id, player):
    """Показать текущий сезонный рейтинг."""
    current = db.get_current_season_number()
    leaderboard = db.get_season_leaderboard(10)
    
    if not leaderboard:
        send(api, peer_id, 
             f"🏆 Сезон {current} только начался. Пока нет участников.\n\n"
             f"Начисляй сезонные очки:\n"
             f"• Дуэль: +10\n"
             f"• PvP победа: +15\n"
             f"• Босс: +20\n"
             f"• Работа: +2")
        return
    
    lines = [f"🏆 Сезонный рейтинг (сезон {current}):\n"]
    medals = ["", "🥈", ""]
    
    for i, p in enumerate(leaderboard, start=1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        lines.append(f"{medal} {p['name']} — {p['season_points']} очков")
    
    lines.append(f"\nТвои очки: {player.get('season_points', 0)}")
    lines.append(
        "\nНаграды топ-3:\n"
        "🥇 1000 монет + титул 'Чемпион'\n"
        "🥈 500 монет + 'Вице-чемпион'\n"
        "🥉 250 монет + 'Бронзовый'"
    )
    send(api, peer_id, "\n".join(lines))


def cmd_history(api, peer_id):
    """Показать историю завершённых сезонов."""
    history = db.get_season_history()
    if not history:
        send(api, peer_id, "История сезонов пуста.")
        return
    
    lines = [" История сезонов:\n"]
    current_season_num = None
    
    for h in history:
        if h["season_number"] != current_season_num:
            current_season_num = h["season_number"]
            lines.append(f"\n🏆 Сезон {current_season_num}:")
        
        # Получаем имя игрока (в таблице seasons имя не хранится)
        pl = db.get_player(h["user_id"], lambda uid: get_name(api, uid))
        
        medal = ["🥇", "🥈", ""][h["position"]-1] if h["position"] <= 3 else f"{h['position']}."
        lines.append(f"  {medal} {pl['name']} — {h['season_points']} очков (+{h['reward_coins']}💰, '{h['title']}')")
    
    send(api, peer_id, "\n".join(lines))