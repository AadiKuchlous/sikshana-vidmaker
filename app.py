from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename
from flask_autoindex import AutoIndex
import tempfile
import openpyxl
import os


app = Flask(__name__)
files_index = AutoIndex(app, os.path.curdir + '/videos', add_url_rules=False)
app.secret_key = 'super secret key'

@app.route('/', methods=["GET", "POST"])
def index():
	pass

@app.route('/new', methods=["GET", "POST"])
def new_xl_form():
	return render_template('xlform.html')

@app.route('/new_data', methods=["GET", "POST"])
def new_vid_data():
	homedir = os.getcwd()
	file = request.files['file']
	fileName = secure_filename(file.filename)
	tmpdir = tempfile.mkdtemp()
	file.save(os.path.join(tmpdir, 'input.xlsx'))
	os.chdir(tmpdir)
	wb = openpyxl.load_workbook(fileName)
	sheets = wb.sheetnames
	os.chdir(homedir)
	session['tmpdir'] = tmpdir
	return render_template('dataform.html', header="", sheets=sheets)

@app.route('/form_submit', methods=["GET", "POST"])
def form_submit():
	print("in form_submit")
	print(os.getcwd())
	if request.method == "POST":
		print("got POST")
		sheetName = request.form["sheetName"]
		videoName = request.form["name"]
		first_slide = request.form["s1"]
		last_slide = request.form["sl"]
		story = str(1 if len(request.form.getlist('story')) == 1 else 0)

		if os.path.exists("videos/{}".format(videoName)):
			return render_template('dataform.html', header="Videos with this name already exist")
		else:
			tmpdir = session.get('tmpdir', None)
			print(tmpdir)
			cmd = './main.py' + ' ' + 'input.xlsx' + ' ' + '"{}"'.format(str(sheetName)) + ' ' + '"{}"'.format(str(tmpdir)) + ' ' + '"{}"'.format(str(videoName)) + ' ' + story + ' ' + str(first_slide) + ' ' + str(last_slide) #+ ' &'
			print(cmd)
			os.system(cmd)
			return 'Sheet: ' + sheetName + '; story: ' + story + '; Video Name: ' + videoName + '; Name available'

@app.route('/files')
@app.route('/files/<path:path>')
def autoindex(path='.'):
	return files_index.render_autoindex(path)