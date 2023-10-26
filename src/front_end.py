import os
from flask import Flask, flash, render_template, request, redirect, url_for, jsonify
import requests
from bson.objectid import ObjectId
from pymongo import MongoClient
# from werkzeug.utils import secure_filename
from gridfs import GridFS
from bson.binary import Binary

app = Flask(__name__)
current_dir = os.getcwd()
app.config['UPLOAD_FOLDER'] = current_dir + '/pics/'
home = 'http://localhost:5001/'
receiver_service_url = 'http://localhost:5001/retrieve_data'

# mongo_database = os.getenv(str('mongo_ip'), 'localhost')
# print('mongo_database/mongo_ip is: ', mongo_database)
# port = str(27017)
# client = MongoClient('mongodb://' + mongo_database + ':' + port + '/')
# print('before connection')
client = MongoClient('mongodb://mongo_ip:27017/')
# print('after connection')
# client = MongoClient('mongodb://localhost:27017/')
db = client['cal_data_db']
collection = db['cal_measurements']
fs = GridFS(db)

@app.route('/')
def index():
    data = list(collection.find())
    return render_template('index.html', data=data)
    # return render_template('index.html')
    # return('<p> Hello </>')

@app.route('/health')
def health():
    return jsonify(status="TRUE")

@app.route('/delete', methods=['POST'])
def delete_data():
    item_id = request.form['id']
    collection.delete_one({'_id': ObjectId(item_id)})
    # requests.get(home)
    return redirect('/')

@app.route('/request_html', methods=['POST'])
def request_html():
    source_serial = {'source_serial': request.form['source_serial_to_send']}
    print(source_serial)
    response = requests.post(receiver_service_url, json=source_serial)  # Trigger the receiving microservice
    print('clicked request html')
    # return redirect('/')
    return response.text

@app.route('/send_data', methods=['GET', 'POST'])
def send_data():
    # source_serial = request.form['source_serial']
    # measure_date = request.form['measure_date']
    # pspd_n = request.form['pspd_n']
    # pspd_tot = request.form['pspd_tot']
    # pspd_mod = request.form['pspd_mod']

    # distribution_image = request.files['distribution_image']
    # bin_distribution_image = Binary(distribution_image.read)
    # dist_pic = request.files['file']
    # dist_id = fs.put(dist_pic, filename=dist_pic.filename)
    # file_id = fs.put(dist_pic, filename=dist_pic.filename)
    # print(file_id)

    if request.method == 'POST':
        file = request.files['file']
        # f.save(f.filename)
        binary_distribution = Binary(file.read())
        cal_data = {
            "serial_number": str(request.form['source_serial']),
            "measurement_date": str(request.form['measure_date']),
            "measurements": {
                "frequency": str(request.form['frequency']),
                "measurement_dist": str(request.form['measure_dist']),
                "pspd_n": str(request.form['pspd_n']),
                "pspd_tot": str(request.form['pspd_tot']),
                "pspd_mod": str(request.form['pspd_mod']),
                "distribution": binary_distribution
            }
        }

    #data = {'source_serial': request.form['source_serial']}
    collection.insert_one(cal_data)
    # requests.post(receiver_service_url)  # Trigger the receiving microservice
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)