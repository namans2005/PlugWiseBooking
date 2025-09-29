from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client['plugwise_db']

# Collections
bookings_collection = db['bookings']
payments_collection = db['payments']

@app.route('/')
def home():
    return render_template('plugwise_me.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    try:
        booking_data = request.json
        
        # Add timestamp to booking data
        booking_data['created_at'] = datetime.utcnow()
        
        # Generate a unique booking ID
        booking_data['booking_id'] = f"PLG{datetime.now().strftime('%Y%m%d%H%M%S')}{booking_data['userId'][-4:]}"
        
        # Store booking data in MongoDB
        booking_result = bookings_collection.insert_one(booking_data)
        
        # Store payment data separately
        payment_data = {
            'booking_id': booking_data['booking_id'],
            'payment_method': booking_data['paymentMethod'],
            'amount': booking_data['totalAmount'],
            'payment_details': {
                'card': booking_data.get('cardNumber'),
                'upi': booking_data.get('upiId'),
                'netbanking': booking_data.get('bankName')
            },
            'payment_status': 'completed',
            'created_at': datetime.utcnow()
        }
        
        payment_result = payments_collection.insert_one(payment_data)
        
        return jsonify({
            'success': True,
            'booking_id': booking_data['booking_id'],
            'message': 'Booking and payment information stored successfully'
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error creating booking: {str(e)}'
        }), 500

@app.route('/api/bookings/user/<user_id>', methods=['GET'])
def get_user_bookings(user_id):
    try:
        bookings = list(bookings_collection.find({'userId': user_id}).sort('createdAt', -1))
        
        # Convert for JSON serialization
        for booking in bookings:
            booking['_id'] = str(booking['_id'])
            booking['date'] = booking['date'].isoformat()
            booking['createdAt'] = booking['createdAt'].isoformat()
        
        return jsonify({
            'success': True,
            'bookings': bookings
        })
        
    except Exception as e:
        print(f"Error fetching user bookings: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error'
        }), 500

@app.route('/api/bookings/<booking_id>', methods=['GET'])
def get_booking(booking_id):
    try:
        booking = bookings_collection.find_one({'booking_id': booking_id})
        if booking:
            # Convert ObjectId to string for JSON serialization
            booking['_id'] = str(booking['_id'])
            return jsonify({
                'success': True,
                'booking': booking
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Booking not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving booking: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)