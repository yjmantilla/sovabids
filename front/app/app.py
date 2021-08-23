import os
from types import TracebackType
from werkzeug.utils import secure_filename
import json
from sovabids.settings import SUPPORTED_EXTENSIONS # This should be deprecated in the future, all should go through the endpoints
from sovabids.dicts import deep_get # This should be deprecated in the future, all should go through the endpoints
import posixpath
from flask import Flask, flash, request, redirect, render_template, session, jsonify, make_response
import requests
from download_zip import download_files
import shutil
import copy
from collections.abc import Iterable
# api-endpoint
SOVABIDS_URL = posixpath.join("http://127.0.0.1:5100",'api','sovabids')
  

app=Flask(__name__)
# Sesions(app)

app.secret_key = "secret key"
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Get current path
path = os.path.dirname(os.path.realpath(__file__))#os.getcwd()
# file Upload
UPLOAD_FOLDER = os.path.join(path, '_uploads')
CONV_FOLDER = os.path.join(path, '_convert')
TEMP_FOLDER = os.path.join(path, '_temp')
# Make directory if uploads is not exists

# Clean server dirs
# TODO: This cleaning should probably be done everytime a new dataset is uploaded
# that is, upon a request gui/upload as a post is made
dirs = [UPLOAD_FOLDER,CONV_FOLDER,TEMP_FOLDER]
for dir in dirs:
    try:
        shutil.rmtree(dir)
    except:
        pass

for x in [UPLOAD_FOLDER,CONV_FOLDER,TEMP_FOLDER]:
    if not os.path.isdir(x):
        os.mkdir(x)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONV_FOLDER'] = CONV_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER
app.config["CACHE_TYPE"] = "null"
# session['filelist'] = []
# session['mappings'] = []
# session['rules'] = {}
# Allowed extension you can set your own
ALLOWED_EXTENSIONS = set([x.replace('.','') for x in SUPPORTED_EXTENSIONS]) # This should be an endpoint

def handle_error(result):
    details = deep_get(result,'error.data.details')
    result_no_details = copy.deepcopy(result)
    if 'data' in result_no_details:
        del result_no_details['error']['data']
    data = json.dumps(result_no_details,indent=4)
    return render_template("error.html", error=data,details=details)

def splitall(path):
    """https://www.oreilly.com/library/view/python-cookbook/0596001673/ch04s16.html"""
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file_rules(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['yaml','txt','yml']

def load_files():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files.get('file')

    if file and allowed_file_rules(file.filename):
        app.logger.info('rule file:{}'.format(file))
        filename = secure_filename(file.filename)
        fpath = os.path.join(app.config['TEMP_FOLDER'], filename)
        file.save(fpath)
        data = {                
        "jsonrpc": "2.0",
        "id": 0,
        "method": "load_rules",
        "params": {
            "rules_path": fpath}
        }
        

        app.logger.info('sovarequest:{}'.format(data))
        # sending get request and saving the response as response object
        sovaurl=posixpath.join(SOVABIDS_URL,'load_rules')
        response = requests.post(url = sovaurl, data = json.dumps(data))
        #app.logger.info('sovaurl:{}'.format(sovaurl))

        app.logger.info('sovaresponse:{}'.format(response))
        result = json.loads(response.content.decode()).get('result',json.loads(response.content.decode()))
        if isinstance(result,Iterable) and 'error' in result:
            return handle_error(result)

        rules = json.loads(response.content.decode())
        rules = rules['result']
        data = json.dumps(rules, indent=4)
        # filename = secure_filename(file.filename)
        # file = open(filename)
        # data = yaml.load(file, Loader=yaml.FullLoader)
        # data =json.dumps(data, indent=4)
        return data


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
        #print(request.files)
        if 'files[]' not in request.files:
            flash('No Files')
            return redirect(request.url)
        files = request.files.getlist('files[]')
        filenames = []
        #https://stackoverflow.com/questions/5826286/how-do-i-use-google-chrome-11s-upload-folder-feature-in-my-own-code/5849341#5849341
        #https://stackoverflow.com/questions/3590058/does-html5-allow-drag-drop-upload-of-folders-or-a-folder-tree
        # Some comments say it wont get all the files?
        # https://stackoverflow.com/a/53058574
        # https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/50#files_and_directories
        # https://developer.mozilla.org/en-US/docs/Web/API/File/webkitRelativePath
        # https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement/webkitdirectory
        for file in files:
            if file :#and allowed_file(file.filename):
                    #accept files, since some eeg formats need sidecars...
                    #we could include all possible sidecar formats too but may mess up stuff
                    # keep like this for now
                #app.logger.info(file.__dict__)
                #useful when cannot debug https://stackoverflow.com/questions/2675028/list-attributes-of-an-object
                fileparts = splitall(file.filename)
                filename = fileparts.pop()# filename is the last, after this fileparts wont have the filename
                filename = secure_filename(filename)
                rel_nested_dir = os.path.join(*fileparts)
                abs_nested_dir = os.path.join(app.config['UPLOAD_FOLDER'],rel_nested_dir)
                os.makedirs(abs_nested_dir,exist_ok=True)
                file.save(os.path.join(abs_nested_dir, filename))
                filenames.append(os.path.join(rel_nested_dir,filename).replace('\\','/'))
        return render_template('exclude_files.html', filenames=filenames)

    else:
        return render_template('upload_files.html')

@app.route("/exclude", methods=['POST', 'GET'])
def exclude():
    if request.method == "POST":

        data = {                
        "jsonrpc": "2.0",
        "id": 0,
        "method": "get_files",
        "params": {
            "rules": {'non-bids':{'eeg_extension':'.vhdr'}},
            "path": app.config['UPLOAD_FOLDER'].replace('\\','/')
            }
        }
        
        #app.logger.info('sovarequest:{}'.format(data))
        # sending get request and saving the response as response object
        urltail='get_files'
        sovaurl=posixpath.join(SOVABIDS_URL,'get_files')
        response = requests.post(url = sovaurl, data = json.dumps(data))
        #app.logger.info('sovaurl:{}'.format(sovaurl))

        app.logger.info('sovaresponse:{}'.format(response))
        result = json.loads(response.content.decode()).get('result',json.loads(response.content.decode()))
        if isinstance(result,Iterable) and 'error' in result:
            return handle_error(result)

        filelist = json.loads(response.content.decode())['result']
        
        filelist = [x.replace('\\','/').replace(app.config['UPLOAD_FOLDER'].replace('\\','/')+'/','') for x in filelist]
        #app.logger.info('filelist : {}'.format(filelist))
        #filelist = os.listdir(app.config['UPLOAD_FOLDER'])
        include = request.form.getlist('records')
        # for filename in filenames:
        #     if filename not in include:
        #         os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #filenames = os.listdir(app.config['UPLOAD_FOLDER'])
        #app.logger.info('include: {}'.format(include))

        filenames = [x for x in filelist if x in include]
        #app.logger.info('finalist : {}'.format(filenames))
        session['filelist']=filenames
        return render_template('files.html', filenames=filenames)
    else:
        return render_template('exclude_files.html')
    
@app.route("/load-rules", methods=['POST', 'GET'])
def load_rules():
    if request.method == 'POST':
        data = load_files()
        return render_template("load_rules.html", rules=data)
    return render_template("load_rules.html")

@app.route("/edit-rules", methods=['POST', 'GET'])
def edit_rules():
    if request.method == 'POST':
        session['general_rules'] = eval(request.form.get('rules'))

        #Make mappings
        urltail='apply_rules'

        data = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": urltail,
        "params": {
            "file_list":[os.path.join(app.config['UPLOAD_FOLDER'],x) for x in session.get('filelist',[])],
            "rules": session.get('general_rules',{}),
            "bids_path": app.config['CONV_FOLDER'].replace('\\','/'),
            "mapping_path":''
            }
        }
        
        app.logger.info('sovarequest:{}'.format(data))
        # sending get request and saving the response as response object
        sovaurl=posixpath.join(SOVABIDS_URL,urltail)
        response = requests.post(url = sovaurl, data = json.dumps(data))
        #app.logger.info('sovaurl:{}'.format(sovaurl))
        
        result = json.loads(response.content.decode()).get('result',json.loads(response.content.decode()))
        if isinstance(result,Iterable) and 'error' in result:
            return handle_error(result)
        #app.logger.info('sovaresponse:{}'.format(result))
        session['mappings'] = result['Individual']
        session['template'] = result['General']
        return redirect('individual_rules')

@app.route("/individual_rules", methods=['POST', 'GET'])
@app.route("/individual_rules/<key>", methods=['POST', 'GET'])
def individual_rules(key=None):
    files = dict(enumerate(session.get('filelist',[])))
    if key:
        rules = json.dumps(session['general_rules'], indent=4)
        if request.method == 'POST':
            # if "form2" in request.form:
            #     data = eval(load_files())
            #     rules = json.dumps(data, indent=4)
            if "form3" in request.form:
                # see https://stackoverflow.com/a/10644186/14068216
                ind_rules = session.get('ind_rules', [])
                rules = eval(request.form.get('rules'))
                data = {'file': key, 'rules': rules}
                if data not in ind_rules:
                    ind_rules.append(data)
                session['ind_rules'] = ind_rules
                print(session['ind_rules'])
                session['mappings'][int(key)] = rules
                app.logger.info('edition:{}'.format(session['mappings'][int(key)]))
                return render_template("individual_rules.html", files=files)

        #return render_template("individual_rules.html", files=files, file=files[int(key)], rules=rules) 
        return render_template("individual_rules.html", files=files, file=files[int(key)], rules=json.dumps(session.get('mappings',[])[int(key)], indent=4))
    return render_template("individual_rules.html", files=files)
    

@app.route("/convert", methods=['POST', 'GET'])
def convert():
    if request.method == 'POST':
        # save edited mappings
        urltail='save_mappings'

        data = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": urltail,
        "params": {
            "general":session.get('template',{}) ,
            "individual": session.get('mappings',[]),
            "path": os.path.join(app.config['CONV_FOLDER'].replace('\\','/'),'code','sovabids','mappings.yml')
            }
        }
        
        app.logger.info('sovarequest:{}'.format(data))
        # sending get request and saving the response as response object
        sovaurl=posixpath.join(SOVABIDS_URL,urltail)
        response = requests.post(url = sovaurl, data = json.dumps(data))
        #app.logger.info('sovaurl:{}'.format(sovaurl))

        result = json.loads(response.content.decode()).get('result',json.loads(response.content.decode()))

        app.logger.info('sovaresponse:{}'.format(response))
        try:
            if isinstance(result,Iterable) and 'error' in result:
                return handle_error(result)
        except:
            pass
        urltail='convert_them'

        data = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": urltail,
        "params": {
            "general":session.get('template',{}) ,
            "individual": session.get('mappings',[]),
            }
        }
        
        app.logger.info('sovarequest:{}'.format(data))
        # sending get request and saving the response as response object
        sovaurl=posixpath.join(SOVABIDS_URL,urltail)
        response = requests.post(url = sovaurl, data = json.dumps(data))
        #app.logger.info('sovaurl:{}'.format(sovaurl))

        result = json.loads(response.content.decode()).get('result',json.loads(response.content.decode()))
        app.logger.info('sovaconvert:{}'.format(result))

        app.logger.info('sovaresponse:{}'.format(response))
        if isinstance(result,Iterable) and 'error' in result:
            return handle_error(result)

        #data = load_files()
        return render_template("ready.html")
    return render_template("convert.html")

@app.route("/download", methods=["GET"])
def download():
    files = getListOfFiles(app.config['CONV_FOLDER'])
    return download_files(files,os.path.join(app.config['TEMP_FOLDER'],'the_zip.zip'))
    # return make_response(jsonify({'data': files}))

def getListOfFiles(dirName):
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
                
    return allFiles


from sovabids.sovarpc import main as back
from sovabids.sovarpc import app as sovapp

import threading

def front(app):
    app.run(host='127.0.0.1',port=5000)#,debug=True)#,threaded=True)

def main():
    t1 = threading.Thread(target=front,args=(app,))
    t2 = threading.Thread(target=back,args=(sovapp,5100))
    t1.start()
    t2.start()
    t2.join()

if __name__ == "__main__":
    main()

