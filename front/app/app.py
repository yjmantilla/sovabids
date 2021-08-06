import os
import re
from werkzeug.utils import secure_filename
import json
from sovabids.settings import SUPPORTED_EXTENSIONS # This should be deprecated in the future, all should go through the endpoints
import yaml

from flask import Flask, flash, request, redirect, render_template, session
# from flask.sesions import Sesions


app=Flask(__name__)
# Sesions(app)

app.secret_key = "secret key"
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Get current path
path = os.getcwd()
# file Upload
UPLOAD_FOLDER = os.path.join(path, 'uploads')

# Make directory if uploads is not exists
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["CACHE_TYPE"] = "null"

# Allowed extension you can set your own
ALLOWED_EXTENSIONS = set([x.replace('.','') for x in SUPPORTED_EXTENSIONS]) # This should be an endpoint


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file_rules(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'yaml'

def load_files():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files.get('file')

    if file and allowed_file_rules(file.filename):
        filename = secure_filename(file.filename)
        file = open(filename)
        data = yaml.load(file, Loader=yaml.FullLoader)
        data =json.dumps(data, indent=4)
        return data


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        filenames = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filenames.append(filename)
        return render_template('exclude_files.html', filenames=filenames)

    else:
        return render_template('upload_files.html')

@app.route("/exclude", methods=['POST', 'GET'])
def exclude():
    if request.method == "POST":
        filenames = os.listdir(app.config['UPLOAD_FOLDER'])
        exclude = request.form.getlist('records')
        for filename in filenames:
            if filename not in exclude:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filenames = os.listdir(app.config['UPLOAD_FOLDER'])
        return render_template('files.html', filenames=filenames)
    else:
        return render_template('exclude_files.html')
    
@app.route("/load-rules", methods=['POST', 'GET'])
def load_rules():
    if request.method == 'POST':
        data = load_files()
        return render_template("load_rules.html", rules=data)
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return render_template("load_rules.html")

@app.route("/edit-rules", methods=['POST', 'GET'])
def edit_rules():
    if request.method == 'POST':
        session['general_rules'] = eval(request.form.get('rules'))
        return redirect('individual_rules')

@app.route("/individual_rules", methods=['POST', 'GET'])
@app.route("/individual_rules/<key>", methods=['POST', 'GET'])
def individual_rules(key=None):
    filenames = os.listdir(app.config['UPLOAD_FOLDER'])
    files = dict(enumerate(filenames))
    if key:
        rules = json.dumps(session['general_rules'], indent=4)
        if request.method == 'POST':
            if "form2" in request.form:
                data = eval(load_files())
                rules = json.dumps(data, indent=4)
            if "form3" in request.form:
                ind_rules = session.get('ind_rules', [])
                rules = eval(request.form.get('rules'))
                data = {'file': key, 'rules': rules}
                if data not in ind_rules:
                    ind_rules.append(data)
                session['ind_rules'] = ind_rules
                print(session['ind_rules'])
                return render_template("individual_rules.html", files=files)

        return render_template("individual_rules.html", files=files, file=files[int(key)], rules=rules) 
      
    return render_template("individual_rules.html", files=files)
    



if __name__ == "__main__":
    app.run(host='127.0.0.1',port=5000,debug=True,threaded=True)