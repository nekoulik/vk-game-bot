"""
Команды магазина: магазин, инвентарь, купить, экипировать.
"""
import db
from config.items import ITEMS, ITEM_EMOJI
from utils.helpers import send


def cmd_shop(api, peer_id):
    """Показать магазин предметов."""
    lines = ["🛒 Магазин предметов\n"]
    for item_id, item in ITEMS.items():
        lines.append(f"{item_id}. {ITEM_EMOJI.get(item_id, '📦')} {item['name']} — {item['price']} монет\n   {item['desc']}\n")
    lines.append("Чтобы купить: купить <номер>")
    send(api, peer_id, "\n".join(lines))


def cmd_inventory(api, peer_id, player):
    """Показать инвентарь игрока."""
    inventory = db.get_inventory(player["user_id"])
    if not inventory:
        send(api, peer_id, "Твой инвентарь пуст.")
        return
    
    lines = ["🎒 Твой инвентарь\n"]
    equipped = db.get_equipment(player["user_id"])
    
    for item_id, count in sorted(inventory.items()):
        if item_id in ITEMS:
            item = ITEMS[item_id]
            eq_mark = " (надето)" if any(eq_id == item_id for eq_id in equipped.values()) else ""
            lines.append(f"{item_id}. {ITEM_EMOJI.get(item_id, '📦')} {item['name']} x{count}{eq_mark}")
    
    lines.append("\nНадеть: экипировать <номер>")
    send(api, peer_id, "\n".join(lines))


def cmd_buy(api, peer_id, player, command):
    """Купить предмет."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, "Формат: купить <номер>")
        return
    
    try:
        item_id = int(parts[1])
    except ValueError:
        send(api, peer_id, "Укажи номер предмета числом")
        return
    
    if item_id not in ITEMS:
        send(api, peer_id, "Такого предмета нет")
        return
    
    item = ITEMS[item_id]
    if player["balance"] < item["price"]:
        send(api, peer_id, f"Недостаточно монет! Нужно {item['price']}")
        return
    
    player["balance"] -= item["price"]
    db.save_player(player)
    db.add_to_inventory(player["user_id"], item_id, 1)
    send(api, peer_id, f"✅ Куплено: {ITEM_EMOJI.get(item_id, '📦')} {item['name']} за {item['price']} монет!")


def cmd_use(api, peer_id, player, command):
    """Экипировать или использовать предмет."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, "Формат: экипировать <номер>")
        return
    
    try:
        item_id = int(parts[1])
    except ValueError:
        send(api, peer_id, "Укажи номер числом")
        return
    
    inventory = db.get_inventory(player["user_id"])
    if item_id not in inventory or inventory[item_id] <= 0:
        send(api, peer_id, "У тебя нет этого предмета!")
        return
    
    if item_id not in ITEMS:
        return
    
    item = ITEMS[item_id]
    
    if item["type"] == "consumable":
        # Расходуемый предмет
        db.remove_from_inventory(player["user_id"], item_id, 1)
        send(api, peer_id, f"Использовано: {ITEM_EMOJI.get(item_id, '📦')} {item['name']}\n{item['desc']}")
    
    elif item["type"] in ["weapon", "armor", "cosmetic"]:
        # Экипируемый предмет
        equipped = db.get_equipment(player["user_id"])
        old = equipped.get(item["type"])
        db.set_equipment(player["user_id"], item["type"], item_id)
        
        msg = f"✅ Надето: {ITEM_EMOJI.get(item_id, '📦')} {item['name']}"
        if old and old in ITEMS:
            msg += f"\n(предыдущее {ITEMS[old]['name']} снято)"
        send(api, peer_id, msg)