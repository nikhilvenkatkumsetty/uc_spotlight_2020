from app.mod_admin.controllers import mod_admin
from app.mod_gdelt.controllers import mod_gdelt
from flask import Flask, render_template


app = Flask(__name__)

app.register_blueprint(mod_admin)
app.register_blueprint(mod_gdelt)


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html')
