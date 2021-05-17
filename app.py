from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory, session
import subprocess
from werkzeug.utils import secure_filename
import tempfile
import openpyxl
import os
import logging
import sys
import shutil
import pyexcel as pe
import re
from pymongo import MongoClient
from datetime import datetime
from flask_assets import Environment, Bundle
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user, LoginManager, logout_user
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
import time

client = MongoClient("mongodb+srv://Aadi:Aadi4321@vidmaker-cluster.vtdh4.mongodb.net/vidmakerdb?retryWrites=true&w=majority")
db = client.vidmakerdb

app = Flask(__name__)

app.secret_key = 'super secret key'

userdb = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
userdb.init_app(app)

from user_model import User

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

assets = Environment(app)
css_bundle = Bundle('navbar.css', output='packed.css')
assets.register('css_all', css_bundle)

gunicorn_logger = logging.getLogger('/home/ubuntu/gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers

base_dir = os.environ.get('VIDMAKER_MAIN')
temp_dir = os.environ.get('VIDMAKER_TEMP')


@app.route('/test', methods=["GET", "POST"])
def test():
	path = request.args.get('path')
	if not path:
		path = "./static/{0}/{1}".format("videos", current_user.id)
	
	path_iter = Path("./{}".format(path))
	
	if path_iter.suffix == ".mp4":
		parts = Path(path).parts
		req_path_parts = parts[1:]
		path = '/'.join(req_path_parts)
		return render_template('video-player.html', src=path)
	
	return render_template('test.html', entries=[x for x in path_iter.iterdir()])

@app.route('/', methods=["GET", "POST"])
def landing():
	return render_template('landing.html')

@app.route('/menu', methods=["GET", "POST"])
@login_required
def menu():
	return render_template('menu.html', page='index')

@app.route('/rename', methods=["GET", "POST"])
def rename():
	oldname = request.form['oldname']
	newname = request.form['new_name']
	cwd = os.getcwd()
	os.chdir('static')
	os.chdir('videos')
	os.chdir(str(current_user.id))
	os.rename(oldname, newname)
	os.chdir(newname)
	os.rename(oldname+"-fast.mp4", newname+"-fast.mp4")
	os.rename(oldname+"-medium.mp4", newname+"-medium.mp4")
	os.rename(oldname+"-slow.mp4", newname+"-slow.mp4")
	os.chdir(cwd)
	return redirect(url_for('show_files'))
	return "Old Name: " + oldname + "; New Name: " + newname + "; " + os.getcwd()

@app.route('/table', methods=["GET", "POST"])
def handson():
#	return request.args.get('tmp')
	tmp = request.args.get('tmp')
	tmpname = re.search("^.*tmp(.*)$", tmp)[1]
	pe.save_book_as(file_name='{}/input.xlsx'.format(tmp), dest_file_name='{0}/templates/{1}.handsontable.html'.format(base_dir, tmpname))
	return render_template('{}.handsontable.html'.format(tmpname))
#	return "Hello World!"

@app.route('/new', methods=["GET", "POST"])
@login_required
def new_xl_form():
	return render_template('xlform.html', page='upload', user=current_user.name)

@app.route('/new_data', methods=["GET", "POST"])
def new_vid_data():
	homedir = os.getcwd()
	file = request.files['myFile']
	fileName = secure_filename(file.filename)
	session['fname'] = file.filename
	tmpdir = tempfile.mkdtemp(dir=temp_dir)
	os.chmod(tmpdir, 0o777)
	file.save(os.path.join(tmpdir, 'input.xlsx'))
	os.chdir(tmpdir)
	wb = openpyxl.load_workbook('input.xlsx')
	sheets = wb.sheetnames
	os.chdir(homedir)
	app.logger.error(homedir)
	session['sheets'] = sheets
	session['tmpdir'] = tmpdir
	app.logger.error(tmpdir)
	return render_template('dataform.html', header="", sheets=sheets, tmp=tmpdir, page='upload')

@app.route('/form_submit', methods=["GET", "POST"])
def form_submit():
	app.logger.error("in form_submit")
	app.logger.error(os.getcwd())
	if request.method == "POST":
		app.logger.error("got POST")
		sheetName = request.form["sheetName"]
		videoName = request.form["name"]
		first_slide = request.form["s1"]
		last_slide = request.form["sl"]
		voice = request.form["gender"]

		userid = str(current_user.id)

		story = str(1 if len(request.form.getlist('story')) == 1 else 0)

		if os.path.exists("videos/{0}/{1}".format(userid, videoName)):
			return render_template('dataform.html', header="Videos with this name already exist", sheets=session['sheets'])
		else:
			tmpdir = session['tmpdir']
			app.logger.error(tmpdir)
			print(os.getcwd())
#			cmd = './main.py' + ' ' + 'input.xlsx' + ' ' + '"{}"'.format(str(sheetName)) + ' ' + '"{}"'.format(str(tmpdir)) + ' ' + '"{}"'.format(str(videoName)) + ' ' + story + ' ' + str(first_slide) + ' ' + str(last_slide) + ' ' + voice.lower() + ' ' + username + ' > log.txt' + ' &'
#			cmd = '/Users/aadikuchlous/Desktop/programming/sikshana-vidmaker/sikshana-vidmaker/main.py' + ' ' + 'input.xlsx' + ' ' + '"{}"'.format(str(sheetName)) + ' ' + '"{}"'.format(str(tmpdir)) + ' ' + '"{}"'.format(str(videoName)) + ' ' + story + ' ' + str(first_slide) + ' ' + str(last_slide) + ' ' + voice.lower() + ' ' + username + ' > log.txt' + ' &'

#			app.logger.error(cmd)
			subprocess.Popen(args=["./main.py", 'input.xlsx', str(sheetName), str(tmpdir), str(videoName), story, str(first_slide), str(last_slide), voice.lower(), userid], env={"PATH": "./:/usr/bin:/usr/local/bin"})
			now = datetime.now()
			dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
			tmpname = "tmp" + re.search("^.*tmp(.*)$", tmpdir)[1]
			entry = {
				'tmp':tmpname,
				'name':videoName,
				'status':"Processing",
				'time sent':dt_string,
				'user': userid
			}
			result=db.data.insert_one(entry)
			story = ("Yes" if story == "1" else "No")
			return render_template('formsubmit.html', fname=session['fname'], sname=sheetName, fslide=first_slide, lslide=last_slide, vname=videoName, story=story, voice=voice, page='upload')

@app.route('/status/', methods=["GET", "POST"])
@login_required
def status():
	data = db.data.find({"user":str(current_user.id)}).sort('_id', -1)
	return render_template('status_page.html', data = data, page='status')

def folder_size(path):
	total = 0
	for entry in path.iterdir():
		if entry.is_file():
			total += entry.stat().st_size
		elif entry.is_dir():
			total += folder_size(entry)
	return total

def convert_bytes(num):
	for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
		if num < 1024.0:
			return f'{num:.1f} {x}'
		num /= 1024.0

@app.route('/files')
@app.route('/files/')
@login_required
def show_files(path='.'):
	path = request.args.get('path')
	if not path:
		path = "./static/{0}/{1}".format("videos", current_user.id)
	
	path_iter = Path("./{}".format(path))
	
	if path_iter.suffix == ".mp4":
		parts = Path(path).parts
		req_path_parts = parts[1:]
		path = '/'.join(req_path_parts)
		return render_template('video-player.html', src=path)
	
	entries = []
	
	for ent in path_iter.iterdir():
		name = ent.name
		if ent.is_dir():
			size = folder_size(ent)
		else:
			size = ent.stat().st_size
		
		date_time = datetime.fromtimestamp(ent.stat().st_atime)

		entries.append({
			"name":name,
			"dt":date_time,
			"size":convert_bytes(size),
			"is_dir":ent.is_dir(),
			"path":ent,
			"ext":ent.suffix
		})
	entries.sort(key=lambda x: x['name'])
	return render_template('files-page.html', entries=entries, preview=request.args.get('preview'))

@app.route('/delete', methods=["GET", "POST"])
def delete():
	# return request.args.get('name'),  os.getcwd(), url_for(request.args.get('name'))
	path = request.form['path-to-delete']
	shutil.rmtree(os.path.join(os.garcwd(), path))
	return redirect(url_for('show_files'))

@app.route('/profile')
@login_required
def profile():
        return render_template("profile.html", page="profile", user=current_user.name)

@app.route('/login')
def login():
        return render_template("login.html", page="login")

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('login'))

    login_user(user, remember=remember)
    return redirect(url_for('menu'))

@app.route('/login-guest', methods=['GET', 'POST'])
def login_guest():
    password = "guest"
    user = User.query.filter_by(email="guest@guest").first()
    login_user(user, remember=True)
    return redirect(url_for('menu'))

@app.route('/signup')
def signup():
        return render_template("signup.html", page="signup")

@app.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists')
        return redirect(url_for('signup'))

    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    userdb.session.add(new_user)
    userdb.session.commit()

    os.mkdir("videos/{}/Stories".format(new_user.id))
    os.mkdir(os.path.join("videos/{}".format(new_user.id), "Other Videos"))

    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('menu'))

if __name__ == "__main__":
	app.run(host='0.0.0.0')
