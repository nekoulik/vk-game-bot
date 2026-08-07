"""
WSGI-приложение для PythonAnywhere.
Красивая заглушка для игрового бота Club Anicoke.
"""

def application(environ, start_response):
    """WSGI-обработчик."""
    path = environ.get('PATH_INFO', '/')
    
    if path == '/' or path == '/index.html':
        status = '200 OK'
        headers = [('Content-type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        
        html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Club Anicoke - Игровой бот</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            animation: fadeIn 0.5s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo-icon { font-size: 80px; margin-bottom: 10px; }
        h1 { color: #667eea; font-size: 32px; margin-bottom: 10px; }
        .subtitle { color: #666; font-size: 16px; margin-bottom: 30px; }
        .status {
            background: #f0f0f0;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .status-item {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .status-item:last-child { margin-bottom: 0; }
        .status-icon { font-size: 20px; margin-right: 10px; }
        .status-text { color: #333; font-size: 14px; }
        .commands {
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .commands h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 18px;
        }
        .command-category { margin-bottom: 10px; }
        .command-category strong {
            color: #764ba2;
            display: block;
            margin-bottom: 5px;
        }
        .command-category span {
            color: #666;
            font-size: 14px;
            line-height: 1.6;
        }
        .vk-button {
            display: block;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            font-size: 16px;
            transition: transform 0.2s;
        }
        .vk-button:hover { transform: translateY(-2px); }
        .footer {
            text-align: center;
            margin-top: 20px;
            color: #999;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <div class="logo-icon">🎮</div>
            <h1>Club Anicoke</h1>
            <div class="subtitle">Игровой бот ВКонтакте</div>
        </div>
        
        <div class="status">
            <div class="status-item">
                <span class="status-icon">🤖</span>
                <span class="status-text"><strong>Статус:</strong> Бот разрабатывается</span>
            </div>
            <div class="status-item">
                <span class="status-icon">📦</span>
                <span class="status-text"><strong>Версия:</strong> 1.0 (beta)</span>
            </div>
        </div>
        
        <div class="commands">
            <h3>📋 Возможности бота:</h3>
            <div class="command-category">
                <strong>💰 Экономика:</strong>
                <span>Баланс, работа, бонусы, магазин, инвентарь</span>
            </div>
            <div class="command-category">
                <strong>️ PvP:</strong>
                <span>Дуэли с игроками, вызовы, ставки</span>
            </div>
            <div class="command-category">
                <strong> Босс:</strong>
                <span>Сражения с боссом, награды</span>
            </div>
            <div class="command-category">
                <strong>🎲 Игры:</strong>
                <span>Камень-ножницы-бумага, угадай число, лотерея</span>
            </div>
            <div class="command-category">
                <strong>🐾 Питомцы:</strong>
                <span>Покупка и активация питомцев</span>
            </div>
            <div class="command-category">
                <strong> Прогресс:</strong>
                <span>Квесты, достижения, сезоны, кланы</span>
            </div>
        </div>
        
        <a href="https://vk.com/im?sel=-197020757" class="vk-button" target="_blank">
            💬 Открыть бота ВКонтакте
        </a>
        
        <div class="footer">
            © 2024 Club Anicoke. Все права защищены.
        </div>
    </div>
</body>
</html>"""
        
        return [html.encode('utf-8')]
    
    else:
        status = '404 Not Found'
        headers = [('Content-type', 'text/plain; charset=utf-8')]
        start_response(status, headers)
        return [b'Strаница не найдена']