#!/bin/bash
python manage.py makemigrations
python manage.py migrate
DJANGO_SUPERUSER_PASSWORD=my_password ./manage.py createsuperuser \
    --no-input \
    --username=my_user \
    --email=my_user@domain.com
python manage.py runserver 0.0.0.0:8000