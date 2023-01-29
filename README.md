# Телеграм бот учета расходов
### Бот предназначен для ведения ежедневного учета расходов пользователя
## Предустановка
1. Установить и настроить Docker и Docker Compose в системе
2. Настроить протокол https на внутренний порт 80
3. Зарегистрировать бота через @BotFather и получить токен
4. Зарегистрировать webhook для бота с полученным https адресом и токеном через get-запрос
`https://api.telegram.org/bot{token}/setWebhook?url={url}`

## Настройка
1. На подобие файла .env_example создать файл .env и заполнить недостающие поля
2. При необходимости отредактировать файл docker-compose.yml
3. Запустить сборку контейнеров с помощью команды `docker-compose up`

## Команды
Бот поддерживает следующие команды:
- /start - запуск бота и сохранение данных пользователя в базе
- /total - показать общие затраты за всё время
- /set_category - добавить категорию
- /delete_category - удалить категорию

## Возможности
Бот имеет следующие возможности:
- добавление\удаление категории
- запись расходов на любой день
- добавление\удаление пунктов расходов в каждой категории
- ежедневно в 23:59 присылает отчет расходов за текущий день