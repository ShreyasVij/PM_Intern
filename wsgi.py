"""
WSGI entrypoint for production (Render/Gunicorn)
Exposes `app` via the Flask factory.
"""
from app.main import create_app

# Gunicorn will import this module and use `app`
app = create_app()
