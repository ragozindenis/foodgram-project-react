![example workflow](https://github.com/ragozindenis/foodgram-project-react/actions/workflows/foodgram-project-react_workflow.yml/badge.svg)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)


# Сайт Foodgram - «Продуктовый помощник». 
## На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

## Реализован Action workflow

* автоматический запуск тестов,
* обновление образов на Docker Hub,
* автоматический деплой на боевой сервер при пуше в главную ветку master.

## Документация API будет доступна после запуска проекта по адресу и копировании файлов в инстуркции по установки:

```
/api/docs/
```

## Запуск проекта на удаленном сервере:

### 1. Клонирования репозитария на локальную машину командой:
```
git clone git@github.com:ragozindenis/foodgram-project-react.git
```
### 2. Далее идем на удаленный сервер:
1. Установка докера:
```
sudo apt-get update
sudo apt install docker.io
```
2. Установка docker-compose:
```
sudo apt-get update
sudo apt-get install docker-compose
```
3. Проверка что все установилось:
```
docker --version
```
```
docker-compose version
```
4. Копируем файлы docker-compose.yaml,nginx.conf, openapi-schema.yml и redoc.html с загруженного репозитария из папки infra и docs на сервер:
```
scp <путь до файла на локальной машине>/<файл> <ваш_username>@<ip/host удаленного сервера>:/home/<ваш_username>/
```
пример:
```
scp /Users/user/Dev/foodgram-project-react/infra/docker-compose.yml admin@127.0.0.1:/home/admin/
scp /Users/user/Dev/foodgram-project-react/infra/nginx/nginx.conf admin@127.0.0.1:/home/admin/
```
Cледующие файлы копировать в папку docs на сервере, если ее нет создать командой mkdir docs на сервере
```
scp /Users/user/Dev/foodgram-project-react/docs/openapi-schema.yml admin@127.0.0.1:/home/admin/docs/
scp /Users/user/Dev/foodgram-project-react/docs/redoc.html admin@127.0.0.1:/home/admin/docs/
```

### 3. Работа с секретами на сайте github:
Перейдите в настройки репозитория Settings, выберите на панели слева Secrets and variables/Actions, нажмите New repository secret и создавайте секреты:
Секреты для Django
```
DB_ENGINE # django.db.backends.postgresql
DB_HOST # db
DB_NAME # postgres
DB_PORT # 5432
POSTGRES_PASSWORD # пароль для подключения к БД (установите свой)
POSTGRES_USER # логин для подключения к базе данных(установите свой)
SECRET_KEY # секретный ключ для файла settings.py
SERVERNAMES # адреса разрешенных серверов через пробел localhost 127.0.0.1 backend ip_server(ip вашего сервера)
```
Секреты для Docker Hub и Deploy на удаленный сервер с Github Actions
```
DOCKER_PASSWORD # логин от Docker Hub
DOCKER_USERNAME # пароль от Docker Hub
HOST # сохраните IP-адрес вашего сервера
PASSPHRASE # пароль для ssh ключа если установлен
SSH_KEY # Скопируйте приватный ключ с компьютера, имеющего доступ к серверу командой cat ~/.ssh/id_rsa
USER # имя пользователя для подключения к серверу
```
### 4. Теперь после push'a репозитария с локальной машины запуститься скрипт.

### 5. Идем на сервер для заключительных команд:
> Сделать миграции командами:
```
sudo docker-compose exec backend python manage.py makemigrations
```
```
sudo docker-compose exec backend python manage.py migrate
```
> Собрать статичные файлы командой:
```
sudo docker-compose exec backend python manage.py collectstatic --no-input
```
> Создать суперпользователя командой:
```
sudo docker-compose exec backend python manage.py createsuperuser
```
> Загрузить ингредиенты в базу данных:
```
sudo docker-compose exec backend python manage.py load_json_ingredients
```
> Админ панель доступна по адресу:
```
/admin/
```
Для полного функционирования сайта нужно в админ панеле создать Теги для рецептов:
Например:
```
Название тега: Завтрак
Цвет: Выбрать в палитре понравившийся
Slug: breakfast 

```
## Проект можно посмотреть по адрессу:
```
130.193.39.207
```
логин и пароль администратора:
admin@example.com
admin12345

