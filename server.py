"""
WSGI сервер для PythonAnywhere.
Импортирует приложение из main.py.
"""
from main import app

application = app