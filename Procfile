# AEIOU AI — Heroku/Railway/Render Procfile
# This file tells the platform how to run your app

web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A config worker -l info
beat: celery -A config beat -l info
