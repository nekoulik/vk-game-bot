"""
Club Anicoke - Игровой бот для ВКонтакте
Главный файл запуска
"""

import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ClubAnicoke')

# Импорт VK API
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

# Импорт наших модулей
from config.settings import VK_TOKEN, VK_GROUP_ID, ADMIN_IDS, DATABASE_PATH
from db.database import init_db, get_connection
from commands.basic import register_basic_commands
from commands.shop import register_shop_commands
from commands.pets import register_pets_commands
from commands.boss import register_boss_commands
from commands.quests import register_quests_commands
from commands.seasons import register_seasons_commands
from commands.games import register_games_commands
from commands.clans import register_clans_commands
from commands.notifications import register_notifications_commands
from commands.admin import register_admin_commands
from utils.helpers import format_number, get_user_info


class ClubAnicokeBot:
    """Главный класс бота"""
    
    def __init__(self):
        self.vk = None
        self.long_poll = None
        self.conn = None
        self.admin_ids = ADMIN_IDS
        self.running = True
        self.commands = {}
        self.message_handlers = []
        
    def init_vk(self):
        """Инициализация VK API"""
        try:
            self.vk_session = vk_api.VkApi(token=VK_TOKEN)
            self.vk = self.vk_session.get_api()
            self.long_poll = VkLongPoll(self.vk_session)
            logger.info("✅ VK API инициализирован")
            logger.info(f"📱 ID группы: {VK_GROUP_ID}")
            logger.info(f"👑 Админы: {self.admin_ids}")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации VK: {e}")
            raise
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            self.conn = get_connection(DATABASE_PATH)
            init_db(self.conn)
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
    
    def register_all_commands(self):
        """Регистрация всех команд"""
        logger.info(" Регистрация команд...")
        
        # Основные команды
        register_basic_commands(self, self.conn)
        
        # Магазин
        register_shop_commands(self, self.conn)
        
        # Питомцы
        register_pets_commands(self, self.conn)
        
        # Босс
        register_boss_commands(self, self.conn)
        
        # Квесты
        register_quests_commands(self, self.conn)
        
        # Сезоны
        register_seasons_commands(self, self.conn)
        
        # Игры
        register_games_commands(self, self.conn)
        
        # Кланы
        register_clans_commands(self, self.conn)
        
        # Уведомления
        register_notifications_commands(self, self.conn)
        
        # Админ-команды (включая /статистика)
        register_admin_commands(self, self.conn, self.admin_ids)
        
        logger.info(f"✅ Зарегистрировано команд: {len(self.commands)}")
        logger.info(f" Список: {', '.join(sorted(self.commands.keys()))}")
    
    def register_command(self, name, handler, description=""):
        """Регистрация одной команды"""
        self.commands[name.lower()] = {
            'handler': handler,
            'description': description
        }
    
    def send_message(self, peer_id, message, attachment=None):
        """Отправка сообщения с обработкой ошибок"""
        try:
            params = {
                'peer_id': peer_id,
                'message': message,
                'random_id': get_random_id()
            }
            if attachment:
                params['attachment'] = attachment
            self.vk.messages.send(**params)
            return True
        except vk_api.exceptions.ApiError as e:
            logger.warning(f"️ Ошибка отправки в {peer_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Критическая ошибка отправки: {e}")
            return False
    
    def process_message(self, event):
        """Обработка входящего сообщения"""
        try:
            user_id = event.user_id
            peer_id = event.peer_id
            text = event.text.strip()
            
            # Игнорируем пустые сообщения
            if not text:
                return
            
            # Получаем информацию о пользователе
            user_info = get_user_info(self.vk, user_id)
            username = user_info.get('first_name', 'Игрок')
            
            logger.info(f"💬 [{peer_id}] {username}: {text[:50]}")
            
            # Разбираем команду
            parts = text.split(maxsplit=1)
            command = parts[0].lower().lstrip('/')
            args = parts[1] if len(parts) > 1 else ""
            
            # Проверяем есть ли такая команда
            if command in self.commands:
                cmd_data = self.commands[command]
                try:
                    cmd_data['handler'](
                        vk=self.vk,
                        peer_id=peer_id,
                        user_id=user_id,
                        username=username,
                        args=args,
                        conn=self.conn,
                        admin_ids=self.admin_ids,
                        bot=self
                    )
                except Exception as e:
                    logger.error(f"❌ Ошибка выполнения команды /{command}: {e}")
                    self.send_message(
                        peer_id,
                        f"⚠️ Произошла ошибка при выполнении команды. Попробуйте позже."
                    )
            else:
                # Неизвестная команда
                self.send_message(
                    peer_id,
                    f"❓ Неизвестная команда: {command}\n\n"
                    f"Напиши /помощь чтобы увидеть список команд"
                )
        
        except Exception as e:
            logger.error(f"❌ Критическая ошибка обработки: {e}")
    
    def run(self):
        """Главный цикл бота"""
        logger.info("🚀 Бот запускается...")
        
        while self.running:
            try:
                logger.info("📡 Подключение к Long Poll...")
                
                for event in self.long_poll.listen():
                    if event.type == VkEventType.MESSAGE_NEW:
                        # Проверяем что сообщение от пользователя (не от бота)
                        if event.from_user or event.from_chat:
                            self.process_message(event)
            
            except vk_api.exceptions.LongpollReadTimeout:
                logger.warning("⏱️ Таймаут Long Poll, переподключение...")
                time.sleep(1)
                continue
            
            except vk_api.exceptions.LongpollError as e:
                logger.error(f"❌ Ошибка Long Poll: {e}")
                logger.info("🔄 Переподключение через 5 секунд...")
                time.sleep(5)
                continue
            
            except Exception as e:
                logger.error(f"💥 Критическая ошибка: {e}")
                logger.info("🔄 Перезапуск через 10 секунд...")
                time.sleep(10)
                continue
    
    def stop(self):
        """Остановка бота"""
        logger.info("🛑 Остановка бота...")
        self.running = False
        if self.conn:
            self.conn.close()
            logger.info(" База данных закрыта")


def main():
    """Точка входа"""
    logger.info("=" * 50)
    logger.info("🎮 Club Anicoke Bot v1.0")
    logger.info("=" * 50)
    logger.info(f"📅 Дата запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    logger.info(f"🐍 Python: {sys.version}")
    logger.info("=" * 50)
    
    # Создаём бота
    bot = ClubAnicokeBot()
    
    try:
        # Инициализация
        bot.init_vk()
        bot.init_database()
        bot.register_all_commands()
        
        # Запуск
        logger.info("✅ Бот готов к работе!")
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("️ Получен сигнал остановки (Ctrl+C)")
        bot.stop()
    
    except Exception as e:
        logger.error(f"💥 Фатальная ошибка: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        logger.info("👋 Бот завершил работу")


if __name__ == '__main__':
    main()