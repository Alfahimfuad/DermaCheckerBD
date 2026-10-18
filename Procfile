web: python manage.py migrate --noinput && python manage.py ensure_render_superuser && gunicorn dermacheckerbd.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 1 --timeout 120
