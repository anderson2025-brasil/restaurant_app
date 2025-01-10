from flask import Flask, request, jsonify  # Import Flask, request, and jsonify
from flask_sqlalchemy import SQLAlchemy  # Import SQLAlchemy for database handling
from geopy.distance import geodesic  # Import geodesic for location calculations

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant_staff.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#import utilities
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app.config['JWT_SECRET_KEY'] = 'your_secret_key' 
# Change this to a secure key
jwt = JWTManager(app)

# Initialize the database
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'owner', 'employee', 'agency'

class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)

class EmployeeProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skills = db.Column(db.String(500), nullable=False)
    availability = db.Column(db.String(200), nullable=False)
    pay_rate = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    preferences = db.Column(db.String(500))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500))

# Create database tables
with app.app_context():
    db.create_all()

# Routes

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and user.password == data['password']:
        token = create_access_token(identity=user.id)
        return jsonify({"access_token": token}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    return jsonify({"message": f"Hello user {current_user_id}"}), 200

@app.route('/')
def home():
    return "Welcome to the Temp Work App!"

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    try:
        user = User(
            name=data['name'],
            email=data['email'],
            password=data['password'],
            role=data['role']
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User created successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/create_employee_profile', methods=['POST'])
def create_employee_profile():
    data = request.json
    try:
        profile = EmployeeProfile(
            user_id=data['user_id'],
            skills=data['skills'],
            availability=data['availability'],
            pay_rate=data['pay_rate'],
            location=data['location'],
            preferences=data.get('preferences', '')
        )
        db.session.add(profile)
        db.session.commit()
        return jsonify({"message": "Employee profile created successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/search_employees', methods=['GET'])
def search_employees():
    try:
        location = request.args.get('location')
        radius = float(request.args.get('radius', 10))  # in miles
        position = request.args.get('position', '').lower()

        business_location = tuple(map(float, location.split(',')))
        employees = EmployeeProfile.query.all()

        results = []
        for employee in employees:
            employee_location = tuple(map(float, employee.location.split(',')))
            distance = geodesic(business_location, employee_location).miles
            if distance <= radius and (position in employee.skills.lower()):
                results.append({
                    "id": employee.id,
                    "skills": employee.skills,
                    "availability": employee.availability,
                    "pay_rate": employee.pay_rate,
                    "distance": round(distance, 2)
                })
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/leave_review', methods=['POST'])
def leave_review():
    data = request.json
    try:
        review = Review(
            reviewer_id=data['reviewer_id'],
            reviewed_id=data['reviewed_id'],
            rating=data['rating'],
            comment=data['comment']
        )
        db.session.add(review)
        db.session.commit()
        return jsonify({"message": "Review submitted successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Main
if __name__ == "__main__":
    app.run(debug=True)
