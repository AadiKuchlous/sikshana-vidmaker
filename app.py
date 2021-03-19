from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename
from flask_autoindex import AutoIndex
import tempfile
import openpyxl
import os
import logging
import sys
import shutil


app = Flask(__name__)
files_index = AutoIndex(app, os.path.curdir + '/videos', add_url_rules=False)
app.secret_key = 'super secret key'
gunicorn_logger = logging.getLogger('/home/ubuntu/gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers

@app.route('/', methods=["GET", "POST"])
def index():
	return render_template('index.html')

@app.route('/new', methods=["GET", "POST"])
def new_xl_form():
	return render_template('xlform.html')

@app.route('/new_data', methods=["GET", "POST"])
def new_vid_data():
	homedir = os.getcwd()
	file = request.files['file']
	fileName = secure_filename(file.filename)
	session['fname'] = file.filename
	tmpdir = tempfile.mkdtemp(dir="/home/ubuntu/sikshana-temp")
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
	return render_template('dataform.html', header="", sheets=sheets)

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
		story = str(1 if len(request.form.getlist('story')) == 1 else 0)

		if os.path.exists("videos/{}".format(videoName)):
			return render_template('dataform.html', header="Videos with this name already exist", sheets=session['sheets'])
		else:
			tmpdir = session['tmpdir']
			app.logger.error(tmpdir)
			cmd = './main.py' + ' ' + 'input.xlsx' + ' ' + '"{}"'.format(str(sheetName)) + ' ' + '"{}"'.format(str(tmpdir)) + ' ' + '"{}"'.format(str(videoName)) + ' ' + story + ' ' + str(first_slide) + ' ' + str(last_slide) + ' > log.txt' + ' &'
			app.logger.error(cmd)
			os.system(cmd)
			return render_template('formsubmit.html', fname=session['fname'], sname=sheetName, fslide=first_slide, lslide=last_slide, vname=videoName)
			return 'Sheet: ' + sheetName + '; story: ' + story + '; Video Name: ' + videoName + '; Name available'

@app.route('/files/')
@app.route('/files/<path:path>')
def autoindex(path='.'):
	return files_index.render_autoindex(path)

@app.route('/delete')
def delete():
	# return request.args.get('name'),  os.getcwd(), url_for(request.args.get('name'))
	shutil.rmtree(os.path.join(os.getcwd(), 'videos', request.args.get('name')))
	return redirect(url_for('autoindex'))

if __name__ == "__main__":
	app.run(host='0.0.0.0')
