from flask import Flask, jsonify, request, render_template, jsonify, send_file
from bson.objectid import ObjectId
from pymongo import MongoClient
import io
import bson
import base64

app = Flask(__name__)
client = MongoClient('mongodb://mongo-ip:27017/')
db = client['cal_data_db']
collection = db['cal_measurements']

@app.route('/view/<mongo_id>', methods=['GET'])
def view_image(mongo_id):
    image_data = collection.find_one({'_id': bson.ObjectId(mongo_id)})
    if image_data is None:
        return 'Image not found', 404
    return send_file(io.BytesIO(image_data['measurements']['distribution']),
                     mimetype=image_data['measurements']['mimetype'])

@app.route('/health')
def health():
    return jsonify(status="UP")

@app.route('/retrieve_data', methods=['POST'])
def retrieve_data():
    source_serial = request.get_json()
    source_serial = source_serial['source_serial']
    source_serial = ObjectId(source_serial)


    # Search for the document with the specified serial number
    result = collection.find_one({"_id": source_serial})
    mongo_id = result['_id']

    if result:
        print("Document found:")
        serial_number = result['serial_number']
        measurement_date = result['measurement_date']

        frequency = result['measurements']['frequency']
        measurement_dist = result['measurements']['measurement_dist']
        pspd_n = result['measurements']['pspd_n']
        pspd_tot = result['measurements']['pspd_tot']
        pspd_mod = result['measurements']['pspd_mod']

        return render_template('html_template.html', serial_number=serial_number, measurement_date=measurement_date,
                               meas_dist=measurement_dist, pspdn=pspd_n, pspdmod=pspd_mod, pspdtot=pspd_tot,
                               freq=frequency, mongo_id=mongo_id)
    else:
        print("No document found with the specified serial number.")

    #data = list(collection.find({}, {'_id': 0}))  # Retrieve data from the database
    #print(source_serial)
    #print(data)
    print('receive was accessed, but data wasnt found')
    return '<html><body><h1>The database data was not found, or access is limited</h1></body></html>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)