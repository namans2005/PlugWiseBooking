from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
import datetime
from bson.objectid import ObjectId
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# MongoDB configuration
client = MongoClient('mongodb://localhost:27017/')
db = client['plugwise_db']
users_collection = db['users']

# Make current_user available in all templates
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data
        
    def get_id(self):
        return str(self.user_data['_id'])
    
    @property
    def name(self):
        return self.user_data.get('name', '')
    
    @property
    def email(self):
        return self.user_data.get('email', '')
    
    @property
    def phone(self):
        return self.user_data.get('phone', '')

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    return User(user_data) if user_data else None

@app.route('/')
def home():
    return render_template('basehome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))

        if email and users_collection.find_one({'email': email}):
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        
        if phone and users_collection.find_one({'phone': phone}):
            flash('Phone number already registered!', 'error')
            return redirect(url_for('register'))

        user_data = {
            'name': name,
            'password': generate_password_hash(password),
            'created_at': datetime.datetime.utcnow()
        }

        if email:
            user_data['email'] = email
        if phone:
            user_data['phone'] = phone

        result = users_collection.insert_one(user_data)
        
        # Log the user in after registration
        user = User(user_data)
        login_user(user)
        
        flash('Registration successful!', 'success')
        return redirect(url_for('home'))

    return render_template('registration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        user_data = None
        if email:
            user_data = users_collection.find_one({'email': email})
        elif phone:
            user_data = users_collection.find_one({'phone': phone})

        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/maps')
def maps():
    return render_template('maps.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/station-info')
def station_info():
    station_id = request.args.get('id')
    return render_template('station-info.html', station_id=station_id)

@app.route('/plugwise_me')
@login_required
def plugwise_me():
    # Get station information from URL parameters
    station_id = request.args.get('station_id')
    station_name = request.args.get('name')
    station_address = request.args.get('address')
    station_type = request.args.get('type')
    station_power = request.args.get('power')
    station_price = request.args.get('price')

    station_info = None
    if station_id:
        station_info = {
            'id': station_id,
            'name': station_name,
            'address': station_address,
            'type': station_type,
            'power': station_power,
            'price': station_price
        }

    return render_template('plugwise_me.html', station_info=station_info)

@app.route('/profile')
@login_required
def profile():
    user_data = db.users.find_one({'_id': ObjectId(current_user.get_id())})
    
    # Get user's bookings from the database
    bookings = list(db.bookings.find({
        'user_id': current_user.get_id()
    }).sort('booking_time', -1))  # Sort by booking time, most recent first
    
    # Convert ObjectId to string for JSON serialization
    for booking in bookings:
        booking['_id'] = str(booking['_id'])
        # Convert datetime to string format
        if isinstance(booking['booking_time'], datetime.datetime):
            booking['booking_time'] = booking['booking_time'].strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('profile.html', user=user_data, bookings=bookings)

@app.route('/recent_bookings')
@login_required
def recent_bookings():
    bookings = []  # Replace with actual booking data
    return render_template('recent_bookings.html', bookings=bookings)

@app.route('/payment')
@login_required
def payment():
    booking = {
        'station_name': request.args.get('selectedStation'),
        'station_id': request.args.get('stationId'),
        'time_slot': request.args.get('selectedTimeSlot'),
        'charger_type': request.args.get('chargerType'),
        'plug_type': request.args.get('plugType'),
        'vehicle_type': request.args.get('vehicleType'),
        'vehicle_brand': request.args.get('vehicleBrand'),
        'vehicle_model': request.args.get('vehicleModel'),
        'vehicle_number': request.args.get('vehicleNumber'),
        'date': request.args.get('date'),
        'user_name': current_user.name,
        'amount': '500',  # You can calculate this based on charger type and duration
        'timeSlots': [
            '9:00 AM',
            '10:00 AM',
            '11:00 AM',
            '2:00 PM',
            '3:00 PM',
            '4:00 PM',
            '5:00 PM',
            '6:00 PM',
            '7:00 PM',
            '8:00 PM',
            '9:00 PM',
            '10:00 PM',
        ]
    }
    return render_template('payment.html', booking=booking)

@app.route('/confirmation', methods=['POST'])
@login_required
def confirmation():
    # Handle payment confirmation
    booking_details = {
        'booking_id': 'BK' + str(random.randint(10000, 99999)),
        'user_id': current_user.get_id(),
        'date': request.form.get('date'),
        'time_slot': request.form.get('timeSlot'),
        'station_name': request.form.get('stationName'),
        'charger_type': request.form.get('chargerType'),
        'plug_type': request.form.get('plugType'),
        'vehicle_type': request.form.get('vehicleType'),
        'vehicle_brand': request.form.get('vehicleBrand'),
        'vehicle_model': request.form.get('vehicleModel'),
        'vehicle_number': request.form.get('vehicleNumber'),
        'amount': request.form.get('amount'),
        'payment_method': request.form.get('paymentMethod'),
        'user_name': current_user.name,
        'payment_status': 'Confirmed',
        'booking_time': datetime.datetime.now(),
        'status': 'Active'
    }
    
    # Save the booking to database
    db.bookings.insert_one(booking_details)
    
    return render_template('confirmation.html', booking=booking_details)

@app.route('/generate_ticket', methods=['POST'])
@login_required
def generate_ticket():
    try:
        # Get form data
        booking_data = {
            'user_id': current_user.get_id(),
            'user_name': current_user.name,
            'vehicle_type': request.form.get('vehicleType'),
            'date': request.form.get('date'),
            'vehicle_brand': request.form.get('vehicleBrand'),
            'vehicle_model': request.form.get('vehicleModel'),
            'vehicle_number': request.form.get('vehicleNumber'),
            'station_name': request.form.get('selectedStation'),
            'station_id': request.form.get('stationId'),
            'time_slot': request.form.get('selectedTimeSlot'),
            'charger_type': request.form.get('chargerType'),
            'booking_time': datetime.datetime.utcnow(),
            'status': 'confirmed',
            'booking_id': f"PLG{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{current_user.get_id()[-4:]}"
        }

        # Store booking in database
        db.bookings.insert_one(booking_data)

        # Add booking to user's bookings
        users_collection.update_one(
            {'_id': ObjectId(current_user.get_id())},
            {'$push': {'bookings': booking_data}}
        )

        flash('Booking successful! Your ticket has been generated.', 'success')
        return redirect(url_for('profile'))

    except Exception as e:
        flash(f'Error generating ticket: {str(e)}', 'error')
        return redirect(url_for('plugwise_me'))

@app.route('/cancel_booking/<booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    try:
        # Find the booking
        booking = db.bookings.find_one({'_id': ObjectId(booking_id)})
        
        if not booking:
            return jsonify({'success': False, 'message': 'Booking not found'})
        
        # Check if the booking belongs to the current user
        if booking['user_id'] != current_user.get_id():
            return jsonify({'success': False, 'message': 'Unauthorized to cancel this booking'})
        
        # Check if the booking is already cancelled
        if booking['status'] == 'cancelled':
            return jsonify({'success': False, 'message': 'Booking is already cancelled'})
        
        # Update booking status to cancelled
        db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': {'status': 'cancelled'}}
        )
        
        # Update the booking in user's bookings array
        users_collection.update_one(
            {
                '_id': ObjectId(current_user.get_id()),
                'bookings._id': ObjectId(booking_id)
            },
            {'$set': {'bookings.$.status': 'cancelled'}}
        )
        
        return jsonify({
            'success': True,
            'message': 'Booking cancelled successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error cancelling booking: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True)