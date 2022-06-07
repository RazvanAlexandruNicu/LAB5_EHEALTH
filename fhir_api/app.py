import json
import os

from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy


project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "fhirrecords.db"))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = database_file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Model
class FhirRecord(db.Model):
    __tablename__ = "records"
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    resource_type = db.Column(db.String(10000), unique=False)
    fhir_record = db.Column(db.String(500000), unique=False)

    def __init__(self, resource_type, fhir_record):
        self.resource_type = resource_type
        self.fhir_record = fhir_record

    def __repr__(self):
        return f"{self.resource_type}({self.id}:{self.fhir_record.__dict__}"

    def serialize(self):
        record = json.loads(self.fhir_record)
        record.update({
            'id': self.id,
        })
        return record


db.create_all()


@app.route('/fhir/all', methods=['GET'])
def get_all_records():
    records = FhirRecord.query.all()
    return make_response(jsonify(records=[e.serialize() for e in records]), 200)


@app.route('/fhir/all/<resource_type>', methods=['GET'])
def get_all_records_by_resource_type(resource_type):
    records = FhirRecord.query.filter_by(resource_type=resource_type).all()
    return make_response(jsonify(records=[e.serialize() for e in records]), 200)


@app.route('/fhir/<id>', methods=['GET'])
def get_record_by_id(id):
    print(id)
    record = FhirRecord.query.get(id)
    if record:
        return make_response(jsonify(record.serialize()), 200)
    else:
        return make_response("Record not found", 404)


@app.route('/fhir/<id>', methods=['DELETE'])
def delete_record_by_id(id):
    record = FhirRecord.query.get(id)
    if record:
        db.session.delete(record)
        db.session.commit()
        return make_response("Resource deleted", 200)
    else:
        return make_response("Record not found", 404)


@app.route('/fhir/<id>', methods=['PUT'])
def update_record_by_id(id):
    data = request.get_json()
    record = FhirRecord.query.get(id)
    if data.get('fhir_record') and record:
        record.fhir_record = json.dumps(data['fhir_record'])
    if data.get('fhir_record') and data.get('fhir_record').get('resourceType') and record:
        # Make sure we dont have inconsistencies with resourceType
        record.resource_type = data['fhir_record']['resourceType']
    db.session.add(record)
    db.session.commit()
    return make_response(jsonify(record.serialize()), 201)


@app.route('/fhir', methods=['POST'])
def create_record():
    data = request.get_json()
    if 'fhir_record' not in data or 'resourceType' not in data['fhir_record']:
        return make_response("fhir_record field is required and it should contain 'resourceType' field")
    print(data['fhir_record'], data['fhir_record']['resourceType'])
    record = FhirRecord(fhir_record=json.dumps(data['fhir_record']), resource_type=data['fhir_record']['resourceType'])
    db.session.add(record)
    db.session.commit()
    return make_response(f"Resource {data['fhir_record']['resourceType']} successfully added", 201)


if __name__ == "__main__":
    app.run(debug=True)