#!/bin/bash
set -e

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Creando superusuario si es necesario..."
python manage.py createsuperuser --noinput || true

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando gunicorn..."
exec gunicorn datapolis_project.wsgi:application --bind 0.0.0.0:8000
