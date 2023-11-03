import os
from flask import Flask, flash, render_template, request, redirect, url_for, jsonify, send_file
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import bson
import io
# from werkzeug.utils import secure_filename
# from gridfs import GridFS


app = Flask(__name__)
current_dir = os.getcwd()
app.config['UPLOAD_FOLDER'] = current_dir + '/pics/'
receiver_service_url = 'http://html-generator:5001/retrieve_data'

client = MongoClient('mongodb://mongo-ip:27017/') #was changed from mongo_ip
db = client['cal_data_db']
collection = db['cal_measurements']


@app.route('/')
def index():
    try:
        # Populate list from mongoDB
        data = list(collection.find())
    except ConnectionFailure:
        # In case of connection error
        data = None
        print("Could not connect to MongoDB")
        return('<p> MongoDB is not accessible </>')
    return render_template('index.html', data=data)

@app.route('/health')
def health():
    return jsonify(status="UP")

#to populate html template coming from html generator
@app.route('/view/<mongo_id>', methods=['GET'])
def view_image(mongo_id):
    image_data = collection.find_one({'_id': bson.ObjectId(mongo_id)})
    if image_data is None:
        return 'Image not found', 404
    return send_file(io.BytesIO(image_data['measurements']['distribution']),
                     mimetype=image_data['measurements']['mimetype'])

@app.route('/delete', methods=['POST'])
def delete_data():
    item_id = request.form['id']
    collection.delete_one({'_id': ObjectId(item_id)})
    return redirect('/')

@app.route('/request_html', methods=['GET', 'POST'])
def request_html():
    source_serial = {'source_serial': request.form.get('source_serial_to_send')}
    print(source_serial)

    try:
        response = requests.post(receiver_service_url, json=source_serial, timeout=10) #ask back_end to serve cert
        response.raise_for_status()
        print('Clicked request html')
        return response.text

    except Timeout:
        print("The request timed out")
        return "Request to receiver service timed out", 504

    except ConnectionError:
        print("Failed to connect to the receiver service")
        return "Could not connect to receiver service", 503

    except RequestException as e:
        print(f"An error occurred while making the request: {str(e)}")
        return "An error occurred while making the request", 500



@app.route('/send_data', methods=['GET', 'POST'])
def send_data():

    if request.method == 'POST':
        file = request.files['file']
        # f.save(f.filename)
        # binary_distribution = Binary(file.read())
        cal_data = {
            "serial_number": str(request.form['source_serial']),
            "measurement_date": str(request.form['measure_date']),
            "measurements": {
                "frequency": str(request.form['frequency']),
                "measurement_dist": str(request.form['measure_dist']),
                "pspd_n": str(request.form['pspd_n']),
                "pspd_tot": str(request.form['pspd_tot']),
                "pspd_mod": str(request.form['pspd_mod']),
                "distribution": bson.Binary(file.read()),
                "mimetype": file.mimetype
            }
        }

    #data = {'source_serial': request.form['source_serial']}
    collection.insert_one(cal_data)
    # requests.post(receiver_service_url)  # Trigger the receiving microservice
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)