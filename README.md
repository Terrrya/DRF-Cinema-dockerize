# Cinema API
<hr>

API service for cinema management writen on DRF

## Installing using GitHub
<hr>

Install PostgreSQL and create db

```python
git clone https://github.com/Terrrya/DRF-Cinema-dockerize.git
cd DRF-Cinema-dockerize
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
set POSTGRES_HOST=<your db hostname>
set POSTGRES_DB=<your db name>
set POSTGRES_USER=<your db username>
set POSTGRES_PASSWORD=<your db user password>
set DJANGO_SECRET_KEY=<your django secret key>
python manage.py migrate
python manage.py runserver
```

## Run with docker
<hr>

Docker should be installed

```python
docker-compose up
```
Open in browser 127.0.0.1:8000

## Getting access
<hr>

- create user via api/user/register/
- get access token via api/user/token/

## Features:
<hr>

- JWT authenticated
- Admin panel: /admin/
- Documentation is located at: /api/doc/swagger/
- Managing orders and tickets
- Creating movies with genres and actors
- Creating cinema halls
- Adding movie sessions
- Filtering movies and movie session


