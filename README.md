# Cinema API
<hr>

API service for cinema management writen on DRF

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

## Installing using GitHub
<hr>

Install PostgreSQL and create db

```python
git clone https://github.com/Terrrya/DRF-Cinema-dockerize.git
cd DRF-Cinema-dockerize
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
create and fill .env file as shown in .env_sample file

## Run with docker
<hr>

Docker should be installed

```python
docker-compose up
```
Open in browser 127.0.0.1:8000/api/ 

## Getting access
<hr>

You can use following superuser:
- Email: admin.user@cinema.com
- Password: 1qazcde3

Or create another one by yourself:
- create user via api/user/register/

To work with token use:
- get access token and refresh token via api/user/token/
- verify access token via api/user/token/verify/
- refresh access token via api/user/token/refresh/
