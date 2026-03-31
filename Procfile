# Procfile — used by Render, Railway, Heroku
# Free tier on Render: https://render.com (spins down after inactivity — upgrade to $7/mo to keep alive)
# Free tier on Railway: https://railway.app ($5 credit/month free)

web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 60
