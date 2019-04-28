Тестовое задание.
Приложения для загрузки данных с источиника. 
http://www.nasdaq.com/symbol/cvx/

## Команды запуска
```bash
docker-compose up --build -d
docker-compose run app python manage.py init_db
docker-compose run app python manage.py parse -w 4 
```
