from flask.cli import FlaskGroup
from app import app


cli = FlaskGroup(app)

# python manage.py run --cert=adhoc -h 0.0.0.0

if __name__ == "__main__":
    cli()
