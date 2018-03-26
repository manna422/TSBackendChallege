from datetime import datetime
from functools import reduce

from dateutil import parser as dateparser
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

PAGINATION_LIMIT = 25
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/nmanna/workspace/TSBackendChallenge/test.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


class Aircraft(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    description = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return '{!s} - {!r}'.format(self.id, self.description)



class LocationRecord(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), primary_key=True, nullable=False)
    datetime = db.Column(db.DateTime, primary_key=True, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    elevation = db.Column(db.Integer, nullable=False)



@app.route('/aircraft', methods=['GET', 'POST', 'DELETE', 'PATCH'])
def aircraft():
    data = request.get_json(force=True)
    current_id = data.get('id', None)
    current_description = data.get('description', None)

    if request.method == 'GET':
        if (current_id):
            return jsonify({'aircrafts': {
                x.id:x.description for x in Aircraft.query.filter_by(id=current_id)
            }})

        else:
            return jsonify({'aircrafts': {x.id:x.description for x in Aircraft.query.all()}})


    if request.method == 'POST':
        if (current_id) and (current_description):

            new_aircraft = Aircraft(
                id=current_id,
                description=current_description
            )

            try:
                db.session.add(new_aircraft)
                db.session.commit()
            except IntegrityError as e:
                return jsonify({'error':'conflicting entry'}), 412

        else:
            return jsonify({'error':'invalid args'}), 400


    if request.method == 'DELETE':
        if current_id:
            Aircraft.query.filter(Aircraft.id == current_id).delete()
            db.session.commit()
        else:
            return jsonify({'error':'invalid args'}), 400


    if request.method == 'PATCH':
        if (current_id) and (current_description):

            new_aircraft = Aircraft(
                id=current_id,
                description=current_description
            )

            Aircraft.query.filter(Aircraft.id == current_id).delete()
            db.session.add(new_aircraft)
            db.session.commit()

        else:
            return jsonify({'error':'invalid args'}), 400


    return jsonify({'status': 'success', 'action': request.method, 'data':data}), 201



@app.route('/location', methods=['GET'])
def location_get():
    results = []
    data = request.get_json(force=True)
    print(data)

    # default to first results page
    page_number = data.get('page_number', 1)
    query_filters = data.get('filters', [])

    supported_filter_keys = ['id', 'datetime', 'longitude', 'latitude', 'elevation']
    supported_comparitors = {
        'eq': lambda x,y: x==y,
        'ne': lambda x,y: x!=y,
        'gt': lambda x,y: x>y,
        'ge': lambda x,y: x>=y,
        'lt': lambda x,y: x<y,
        'le': lambda x,y: x<=y,
    }
    filter_args = []

    for criteria in query_filters:
        if len(criteria) != 3:
            return jsonify({'error':'invalid filter args'}), 400

        key, comparitor, value = criteria
        if (key not in supported_filter_keys) or (comparitor not in supported_comparitors):
            return jsonify({'error':'invalid filter args'}), 400

        filter_args.append(supported_comparitors[comparitor](
            LocationRecord.__dict__[key],
            value
        ))


    # compounding list of filters using the reduce operator
    compounded_query = reduce(lambda x,y: x.filter(y), filter_args, LocationRecord.query)
    paginated_results = compounded_query.paginate(
        page_number,
        PAGINATION_LIMIT,
        error_out=False
    )

    results = [
        {
            'id': item.id,
            'datetime': datetime.isoformat(item.datetime),
            'longitude': item.longitude,
            'latitude': item.latitude,
            'elevation': item.elevation
        }
        for item in paginated_results.items
    ]

    return jsonify({
        'status': 'success',
        'action': request.method,
        'query':data,
        'results': results,
        'page_current': page_number,
        'page_total': paginated_results.pages
    }), 201

    return jsonify({'status': 'success', 'action': request.method, 'data':data}), 201



@app.route('/location', methods=['POST', 'DELETE', 'PATCH'])
def location():
    data = request.get_json(force=True)

    current_id = data.get('id', None)
    current_datetime = data.get('datetime', None)
    current_longitude = data.get('longitude', None)
    current_latitude = data.get('latitude', None)
    current_elevation = data.get('elevation', None)

    # convert timestring to datetime object
    if current_datetime:
        current_datetime = dateparser.parse(current_datetime)


    if request.method == 'POST':
        if all([
            current_id,
            current_datetime,
            current_longitude,
            current_latitude,
            current_elevation
        ]):
            new_location_record = LocationRecord(
                id=current_id,
                datetime=current_datetime,
                longitude=current_longitude,
                latitude=current_latitude,
                elevation=current_elevation
            )

            try:
                db.session.add(new_location_record)
                db.session.commit()
            except IntegrityError as e:
                return jsonify({'error':'conflicting entry'}), 412

        else:
            return jsonify({'error':'invalid args'}), 400


    if request.method == 'DELETE':
        if (current_id) and (current_datetime):
            LocationRecord.query.filter(
                (LocationRecord.id == current_id) and (LocationRecord.datetime == current_datetime)
            ).delete()

            db.session.commit()

        else:
            return jsonify({'error':'invalid args'}), 400


    if request.method == 'PATCH':
        if all([
            current_id,
            current_datetime,
            current_longitude,
            current_latitude,
            current_elevation
        ]):
            new_location_record = LocationRecord(
                id=current_id,
                datetime=current_datetime,
                longitude=current_longitude,
                latitude=current_latitude,
                elevation=current_elevation
            )

            LocationRecord.query.filter(
                (LocationRecord.id == current_id) and (LocationRecord.datetime == current_datetime)
            ).delete()

            db.session.add(new_location_record)
            db.session.commit()

        else:
            return jsonify({'error':'invalid args'}), 400

    return jsonify({'status': 'success', 'action': request.method, 'data':data}), 201


@app.route('/reset')
def reset_databases():
    db.drop_all()
    db.create_all()
    return "Resetting DB..."


if __name__ == '__main__':
    app.run()
