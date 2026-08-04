import time

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

import game

longpoll = VkBotLongPoll(game.session, game.GROUP_ID)


def main():
    print("Бот запущен (Long Poll)")
    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    message = event.obj.message
                    user_id = message.get("from_id")
                    peer_id = message.get("peer_id")
                    text = message.get("text", "")
                    if not user_id or not peer_id or not text:
                        continue
                    try:
                        game.handle(user_id, peer_id, text)
                    except Exception as e:
                        print("Ошибка в обработчике:", e)
        except Exception as e:
            print("Ошибка Long Poll:", e)
            time.sleep(2)


if __name__ == "__main__":
    main()