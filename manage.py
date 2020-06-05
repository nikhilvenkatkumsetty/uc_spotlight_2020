from flask.cli import FlaskGroup
from app import app


cli = FlaskGroup(app)

# Command Line - python manage.py run --cert=adhoc -h 127.0.0.1

if __name__ == "__main__":
    cli()
