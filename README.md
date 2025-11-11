# Система управления задачами

API для управления задачами, проектами и командами на базе FastAPI.

## Установка

1. Клонируйте репозиторий
2. Создайте виртуальное окружение:

python -m venv venv
venv\Scripts\activate  

3. Установите зависимости:

pip install -r requirements.txt

4. Примените миграции базы данных:

alembic upgrade head

5. Запустите сервер:

uvicorn app.main:app --reload

## API Документация

После запуска сервера документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc