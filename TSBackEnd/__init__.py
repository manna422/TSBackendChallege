from datetime import datetime
from functools import reduce

from dateutil import parser as dateparser
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError


# APP, DB INITIALIZATION

DEFAULT_PAGINATION_LIMIT = 25
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# MODEL DECLATAION

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


# ROUTE DECLATAION

@app.route('/aircraft', methods=['GET', 'POST', 'DELETE', 'PATCH'])
def aircraft():
    '''
    Handle insertion, update, delete and query of aircraft description data
    '''
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

            # handle conflicting entries
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

            # delete old entries if they exist and replace with new ones
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

    # default to first results page
    page_number = data.get('page_number', 1)
    query_filters = data.get('filters', [])
    sort_criterion = data.get('sort', [])

    # supported arguments for sorting and filtering
    suported_keys = ['id', 'datetime', 'longitude', 'latitude', 'elevation']
    supported_comparitors = {
        'eq': lambda x,y: x==y,
        'ne': lambda x,y: x!=y,
        'gt': lambda x,y: x>y,
        'ge': lambda x,y: x>=y,
        'lt': lambda x,y: x<y,
        'le': lambda x,y: x<=y,
    }
    supported_sort_directions = ['asc', 'desc']

    filter_args = []
    sort_args = []

    for criteria in query_filters:
        if len(criteria) != 3:
            return jsonify({'error':'invalid filter args'}), 400

        key, comparitor, value = criteria
        if (key not in suported_keys) or (comparitor not in supported_comparitors):
            return jsonify({'error':'invalid filter args'}), 400

        filter_args.append(supported_comparitors[comparitor](
            LocationRecord.__dict__[key],
            value
        ))


    # compounding list of filters using the reduce operator
    filtered_query = reduce(lambda x,y: x.filter(y), filter_args, LocationRecord.query)


    for criteria in sort_criterion:
        if len(criteria) != 2:
            return jsonify({'error':'invalid sorting args'}), 400

        key, direction = criteria
        if (key not in suported_keys) or (direction not in supported_sort_directions):
            return jsonify({'error':'invalid sorting args'}), 400

        sort_args.append('{!s} {!s}'.format(key, direction))


    # sorting data using reduce to concatenate requirements
    sorted_filtered_query = reduce(lambda x,y: x.order_by(y), sort_args, filtered_query)


    paginated_results = sorted_filtered_query.paginate(
        page_number,
        data.get('page_limit', DEFAULT_PAGINATION_LIMIT),
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

    # grab keys
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

            # handle conflicting entries
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

            # delete old entries if they exist and replace with new ones
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
    '''
    Purely for debugging
    '''
    db.drop_all()
    db.create_all()
    return "Resetting DB..."

