from flask.cli import FlaskGroup
from app import app


cli = FlaskGroup(app)

# python manage.py run --cert=adhoc

if __name__ == "__main__":
    cli()
