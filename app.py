from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from models import db, User, DiningPlace, Booking
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from config import Config
from decorators import admin_api_key_required
from dateutil.parser import parse

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)


@app.route("/api")
def home():
    return "Dining Reservation System"

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    new_user = User(username=username, password=password, email=email)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'status': 'Account successfully created', 'status_code': 200}), 200

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        expires = timedelta(days=1)  # Token expires in 1 day
        access_token = create_access_token(identity=user.id, expires_delta=expires)
        return jsonify({'status': 'Login successful', 'status_code': 200, 'access_token': access_token}), 200
    else:
        return jsonify({'status': 'Incorrect username/password provided. Please retry', 'status_code': 401}), 401

@app.route('/api/dining-place/create', methods=['POST'])
@admin_api_key_required
def create_dining_place():
    data = request.get_json()
    name = data.get('name')
    address = data.get('address')
    phone_no = data.get('phone_no')
    website = data.get('website')
    operational_hours = data.get('operational_hours',{})
    open_time = operational_hours.get('open_time')
    close_time = operational_hours.get('close_time')
    booked_slots = data.get('booked_slots',[])

    new_dining_place = DiningPlace(name=name, address=address, phone_no=phone_no, website= website, open_time=open_time, close_time=close_time, booked_slots=booked_slots)
    db.session.add(new_dining_place)
    db.session.commit()

    return jsonify({'message': new_dining_place.name+' added successfully', 'place_id': new_dining_place.id}), 200

@app.route('/api/dining-place', methods=['GET'])
def get_dining_places():
    search_query = request.args.get('name', '')

    # Search for dining places by name
    places = DiningPlace.query.filter(DiningPlace.name.like(f'%{search_query}%')).all()

    # Format the response data
    results = []
    for place in places:
        results.append({
            'place_id': place.id,
            'name': place.name,
            'address': place.address,
            'phone_no': place.phone_no,
            'website': place.website,
            'operational_hours': {
                'open_time': place.open_time.strftime('%H:%M:%S'),
                'close_time': place.close_time.strftime('%H:%M:%S')
            },
            'booked_slots': [
                {
                    'start_time': slot['start_time'],
                    'end_time': slot['end_time']
                }
                for slot in place.booked_slots
            ]
        })

    return jsonify({'results': results}), 200

@app.route('/api/dining-place/availability', methods=['GET'])
def get_dining_place_availability():
    place_id = request.args.get('place_id')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    if not place_id or not start_time or not end_time:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        start_time_dt = parse(start_time)
        end_time_dt = parse(end_time)
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    dining_place = DiningPlace.query.get(place_id)

    if not dining_place:
        return jsonify({"error": "Dining place not found"}), 404

    available = True
    next_available_slot = None

    bookings = Booking.query.filter_by(place_id=place_id).all()
    for booking in bookings:
        if start_time_dt < booking.end_time and end_time_dt > booking.start_time:
            available = False
            next_available_slot = booking.end_time.isoformat() if booking.end_time > end_time_dt else next_available_slot
            break

    response = {
        "place_id": dining_place.id,
        "name": dining_place.name,
        "phone_no": dining_place.phone_no,
        "available": available,
        "next_available_slot": next_available_slot
    }

    return jsonify(response)

from datetime import datetime
import pytz

@app.route('/api/dining-place/book', methods=['POST'])
@jwt_required()  # Protect the endpoint with JWT authentication
def book_dining_place():
    current_user_id = get_jwt_identity()  # Get current user's ID from JWT token
    data = request.get_json()
    place_id = data.get('place_id')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    try:
        # Parse datetime strings and replace 'Z' with '+00:00' for UTC conversion
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    # Convert parsed datetimes to UTC timezone
    utc = pytz.UTC
    start_time_utc = start_time.astimezone(utc)
    end_time_utc = end_time.astimezone(utc)

    place = DiningPlace.query.get(place_id)
    if not place:
        return jsonify({'status': 'Place not found', 'status_code': 404}), 404

    # Check if the slot is already booked
    bookings = Booking.query.filter_by(place_id=place_id).all()
    for booking in bookings:
        booking_start = datetime.fromisoformat(booking.start_time.replace('Z', '+00:00')).replace(tzinfo=utc)
        booking_end = datetime.fromisoformat(booking.end_time.replace('Z', '+00:00')).replace(tzinfo=utc)
        if start_time_utc < booking_end and end_time_utc > booking_start:
            return jsonify({'status': 'Slot is not available at this moment, please try some other place', 'status_code': 400}), 400

    # Add the booking to the bookings table
    new_booking = Booking(user_id=current_user_id, place_id=place_id, start_time=start_time_utc, end_time=end_time_utc)
    db.session.add(new_booking)
    db.session.commit()

    return jsonify({'status': 'Slot booked successfully', 'status_code': 200}), 200


if __name__ == '__main__':
    app.run(debug=True)

