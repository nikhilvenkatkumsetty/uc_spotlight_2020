from flask import Blueprint, request, render_template, redirect, url_for
import sqlite3
import os


mod_admin = Blueprint('admin', __name__, url_prefix='/admin', template_folder='admin')


@mod_admin.route('/', methods=['GET'])
def index():
    return redirect(url_for('.configure'))


@mod_admin.route('/configure', methods=['GET', 'POST'])
def configure():

    if request.method == 'GET':

        return render_template('admin/configure.html')

    if request.method == 'POST':

        # Connect to Local Configuration DB
        con = sqlite3.connect(f'{os.path.dirname(mod_admin.root_path)}/info.db')
        cur = con.cursor()

        # Collect Form Inputs
        esri_url  = request.form.get('esri_url')
        username  = request.form.get('username')
        password  = request.form.get('password')

        # Write Values into SQLite DB
        cur.execute(f"insert or replace into config values ('{esri_url}', '{username}', '{password}')")
        con.commit()

        return f'Portal Information Configured'
