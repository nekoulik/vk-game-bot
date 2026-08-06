"""
Команды питомцев: магазин питомцев, мои питомцы, купить питомца, активировать.
"""
import db
from config.pets import PETS
from utils.helpers import send


def cmd_pets_shop(api, peer_id, user_id):
    """Показать магазин питомцев."""
    lines = ["🐾 Магазин питомцев:\n"]
    player_pets = db.get_player_pets(user_id)
    owned_pet_ids = [p["pet_id"] for p in player_pets]
    
    for pet_id, pet in PETS.items():
        if pet_id in owned_pet_ids:
            active_mark = " ✅ (активен)" if any(p["pet_id"] == pet_id and p["is_active"] for p in player_pets) else " (куплен)"
            lines.append(f"{pet['emoji']} {pet['name']} — {pet['price']} монет{active_mark}\n   {pet['desc']}")
        else:
            lines.append(f"{pet['emoji']} {pet['name']} — {pet['price']} монет\n   {pet['desc']}")
    
    lines.append("\nКупить: купить питомца <id>")
    lines.append("Активировать: активировать <id>")
    send(api, peer_id, "\n".join(lines))


def cmd_my_pets(api, peer_id, user_id):
    """Показать питомцев игрока."""
    owned = db.get_player_pets(user_id)
    if not owned:
        send(api, peer_id, "У тебя пока нет питомцев. Загляни в магазин: питомцы")
        return
    
    lines = ["🐾 Твои питомцы:\n"]
    for p in owned:
        pet = PETS.get(p["pet_id"])
        if pet:
            active_mark = " ✅ АКТИВЕН" if p["is_active"] else ""
            lines.append(f"{pet['emoji']} {pet['name']}{active_mark}\n   {pet['desc']}")
    
    send(api, peer_id, "\n".join(lines))


def cmd_buy_pet(api, peer_id, player, command):
    """Купить питомца."""
    # Парсим: "купить питомца 1" или "купить питомца Собака"
    parts = command.split()
    
    if len(parts) < 3:
        send(api, peer_id, "Формат: купить питомца <id>")
        return
    
    # Пробуем получить ID (последнее слово)
    pet_arg = parts[-1]
    
    # Проверяем - число или название
    try:
        pet_id = int(pet_arg)
    except ValueError:
        # Если не число - ищем по названию
        pet_name = pet_arg.lower()
        found = False
        for pid, pet in PETS.items():
            if pet["name"].lower() == pet_name:
                pet_id = pid
                found = True
                break
        
        if not found:
            send(api, peer_id, f"Питомец '{pet_name}' не найден!")
            return
    
    if pet_id not in PETS:
        send(api, peer_id, "Такого питомца нет!")
        return
    
    pet = PETS[pet_id]
    if player["balance"] < pet["price"]:
        send(api, peer_id, f"Недостаточно монет! Нужно {pet['price']}")
        return
    
    owned = db.get_player_pets(player["user_id"])
    if any(p["pet_id"] == pet_id for p in owned):
        send(api, peer_id, f"У тебя уже есть {pet['emoji']} {pet['name']}!")
        return
    
    player["balance"] -= pet["price"]
    db.save_player(player)
    db.buy_pet(player["user_id"], pet_id)
    send(api, peer_id, f"🎉 Ты купил {pet['emoji']} {pet['name']}!\n{pet['desc']}\n\nАктивируй: активировать {pet_id}")


def cmd_activate_pet(api, peer_id, user_id, command):
    """Активировать питомца."""
    parts = command.split()
    if len(parts) < 2:
        send(api, peer_id, "Формат: активировать <id>")
        return
    
    try:
        pet_id = int(parts[1])
    except ValueError:
        send(api, peer_id, "ID должен быть числом")
        return
    
    owned = db.get_player_pets(user_id)
    if not any(p["pet_id"] == pet_id for p in owned):
        send(api, peer_id, "У тебя нет этого питомца!")
        return
    
    db.activate_pet(user_id, pet_id)
    pet = PETS[pet_id]
    send(api, peer_id, f"✅ {pet['emoji']} {pet['name']} активирован!\n{pet['desc']}")