cd ~/vk-game-bot

# Создай server.py который импортирует из main.py
cat > server.py << 'EOF'
"""
WSGI сервер для PythonAnywhere.
Импортирует приложение из main.py.
"""
from main import app

application = app
EOF

# Проверь что server.py создан
cat server.py

# Проверь импорты
python3 -c "from server import app; print('✅ server OK')"

# Перезагрузи WSGI
touch /var/www/nekoulik_pythonanywhere_com_wsgi.py