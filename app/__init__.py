from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

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
            return jsonify({'aircrafts': {x.id:x.description for x in Aircraft.query.filter_by(id=current_id)}})
        else:
            return jsonify({'aircrafts': {x.id:x.description for x in Aircraft.query.all()}})


    if request.method == 'POST':
        if (current_id) and (current_description):

            new_aircraft = Aircraft(
                id=current_id,
                description=current_description
            )

            db.session.add(new_aircraft)
            db.session.commit()

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


    return jsonify({'status': 'success'}), 201


@app.route('/location', methods=['GET', 'POST', 'DELETE', 'PATCH'])
def location():
    data = request.get_json(force=True)

    # if request.method == 'POST':



    print(request.method)
    print(data)
    return jsonify({'task': data}), 201



if __name__ == '__main__':
    # db.drop_all()
    # db.create_all()
    app.run()
