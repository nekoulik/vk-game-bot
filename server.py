cd ~/vk-game-bot

cat > server.py << 'EOF'
"""
WSGI сервер для PythonAnywhere.
Импортирует приложение из main.py.
"""
from main import app

application = app
EOF

cat server.py

python3 -c "from server import app; print('✅ server OK')"

touch /var/www/nekoulik_pythonanywhere_com_wsgi.py