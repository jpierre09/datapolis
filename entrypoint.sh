#!/bin/bash
set -e

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Creando superusuario si es necesario..."
python manage.py createsuperuser --noinput || true

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

if [ "$DJANGO_DEBUG" = "1" ]; then
    echo "Iniciando servidor de desarrollo de Django (runserver)..."
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "Iniciando gunicorn para producción..."
    exec gunicorn datapolis_project.wsgi:application --bind 0.0.0.0:8000
fi
