"""
Команды для сражения с боссом.
"""
import random
from utils.helpers import send, format_number
from db.players import increment_daily_stat
from config.shop import WEAPONS
import db


def cmd_boss(api, peer_id, user_id):
    """Показать информацию о боссе."""
    boss = db.boss.get_boss()
    
    if not boss or not boss['is_active']:
        if db.boss.get_boss_cooldown():
            text = (
                " *Босс не активен!*\n\n"
                "Напиши *создать босса* чтобы вызвать нового!"
            )
        else:
            text = (
                "⏱️ *Босс отдыхает...*\n\n"
                "Следующий босс появится через несколько часов."
            )
        send(api, peer_id, text)
        return
    
    hp_percent = (boss['current_hp'] / boss['max_hp']) * 100
    
    bars = 10
    filled = int(bars * hp_percent / 100)
    hp_bar = "█" * filled + "░" * (bars - filled)
    
    text = (
        f"👹 *Босс {boss['level']} уровня!*\n\n"
        f"❤️ Здоровье: {boss['current_hp']}/{boss['max_hp']}\n"
        f"📊 [{hp_bar}] {hp_percent:.1f}%\n"
        f"🏆 Награда: {format_number(boss['reward'])} монет\n\n"
        f"⚔️ Напиши *атака* или *атаковать* чтобы сразиться!"
    )
    send(api, peer_id, text)


def cmd_spawn_boss(api, peer_id, user_id):
    """Создать нового босса (только для админов)."""
    if not db.boss.get_boss_cooldown():
        send(api, peer_id, "⏱️ Босс ещё не восстановился! Подожди несколько часов.")
        return
    
    level = random.randint(1, 3)
    db.boss.spawn_boss(level)
    
    max_hp = 1000 * level
    reward = 500 * level
    
    text = (
        f"👹 *ПОЯВИЛСЯ НОВЫЙ БОСС {level} УРОВНЯ!*\n\n"
        f"❤️ Здоровье: {max_hp}\n"
        f"🏆 Награда: {format_number(reward)} монет\n\n"
        f"⚔️ Все игроки могут атаковать!\n"
        f"Напиши *атака* чтобы сразиться!"
    )
    send(api, peer_id, text)


def cmd_attack_boss(api, peer_id, user_id, player):
    """Атаковать босса."""
    boss = db.boss.get_boss()
    
    if not boss or not boss['is_active']:
        send(api, peer_id, "👹 Босс не активен! Напиши *босс* чтобы проверить.")
        return
    
    # 1. Базовый урон от уровня
    damage = db.boss.get_boss_damage(user_id)
    
    # 2. БОНУС ОТ ОРУЖИЯ
    equipped_weapon = player.get("equipped_weapon")
    if equipped_weapon:
        weapon_data = next((w for w in WEAPONS.values() if w["item_id"] == equipped_weapon), None)
        if weapon_data:
            damage += weapon_data["damage"]
    
    # 3. БОНУС ОТ ПИТОМЦА (множитель)
    pet_bonus_damage = player.get("pet_bonus_damage", 0)
    if pet_bonus_damage > 0:
        damage = int(damage * (1 + pet_bonus_damage))
    
    # Атакуем с учётом всех бонусов
    actual_damage, boss_killed, reward = db.boss.attack_boss(user_id, damage)
    
    # ОТСЛЕЖИВАНИЕ КВЕСТА "БОСС"
    increment_daily_stat(player["user_id"], "boss_damage", actual_damage)
    
    if boss_killed:
        player['balance'] = int(player.get('balance', 0)) + reward
        db.save_player(player)
        
        text = (
            f"⚔️ Ты нанёс {actual_damage} урона боссу!\n\n"
            f"🎉 *БОСС УБИТ!*\n"
            f"🏆 Ты получаешь {format_number(reward)} монет!\n\n"
            f"Следующий босс появится через 6 часов."
        )
    else:
        new_hp = boss['current_hp'] - actual_damage
        hp_percent = (new_hp / boss['max_hp']) * 100
        text = (
            f"️ Ты нанёс {actual_damage} урона боссу!\n\n"
            f"❤️ Осталось HP: {new_hp}/{boss['max_hp']}\n"
            f" Здоровье: {hp_percent:.1f}%\n\n"
            f"Продолжай атаковать!"
        )
    
    send(api, peer_id, text)