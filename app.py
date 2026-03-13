from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import bcrypt
from sqlalchemy import text
import random
import time
from datetime import datetime, date
from config import Config
from flask_mail import Mail, Message

app = Flask(__name__)
app.config.from_object(Config)

mail = Mail(app)
# -----------------------------
# MySQL Configuration
# -----------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/flaskdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)

otp_storage = {}
otp_time = {}

# -----------------------------
# User Model
# -----------------------------
# -----------------------------
# User Model
# -----------------------------
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    gender = db.Column(db.String(10))
    height = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    goal = db.Column(db.String(50))

# -----------------------------
# Daily Activity Model
# -----------------------------
class DailyActivity(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    steps = db.Column(db.Integer, default=0)
    water_ml = db.Column(db.Integer, default=0)
    calories = db.Column(db.Integer, default=0)
    activity_date = db.Column(db.Date, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'activity_date', name='unique_user_day'),
    )


# -----------------------------
# Create Tables
# -----------------------------
with app.app_context():

    db.create_all()

    result = db.session.execute(text("SHOW COLUMNS FROM user LIKE 'full_name'"))
    column_exists = result.fetchone()

    if not column_exists:
        db.session.execute(text(
            "ALTER TABLE user ADD COLUMN full_name VARCHAR(100)"
        ))
        db.session.commit()


# -----------------------------
# Home Route
# -----------------------------
@app.route("/")
def home():
    return jsonify({"message": "Flask + MySQL Connected 🚀"})


# -----------------------------
# Register API
# -----------------------------
@app.route('/api/auth/signup', methods=['POST'])
def signup():

    data = request.get_json()

    full_name = data['full_name']
    email = data['email']
    password = data['password']
    gender = data.get('gender')
    height = data.get('height')
    weight = data.get('weight')
    goal = data.get('goal')

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode("utf-8")

    user = User(
        full_name=full_name,
        email=email,
        password=hashed,
        gender=gender,
        height=height,
        weight=weight,
        goal=goal
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"})


# -----------------------------
# Login API
# -----------------------------
# -----------------------------
# Login API
# -----------------------------
@app.route("/api/auth/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):

        return jsonify({
    "message": "Login Successful",
    "user": {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "gender": user.gender,
        "height": user.height,
        "weight": user.weight,
        "goal": user.goal
    }
})
    return jsonify({"error": "Invalid password"}), 401

# -----------------------------
# Update Profile
# -----------------------------
@app.route("/update_profile/<int:user_id>", methods=["POST"])
def update_profile(user_id):

    data = request.get_json()

    gender = data.get("gender")
    height = data.get("height")
    weight = data.get("weight")
    goal = data.get("goal")

    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    user.gender = gender
    user.height = height
    user.weight = weight
    user.goal = goal

    db.session.commit()

    return jsonify({"message": "Profile updated successfully"})


# -----------------------------
# Forgot Password
# -----------------------------
@app.route("/forgot-password", methods=["POST"])
def forgot_password():

    data = request.get_json()
    email = data.get("email")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    otp = random.randint(100000, 999999)

    otp_storage[email] = str(otp)
    otp_time[email] = time.time()

    try:

        msg = Message(
            "FitFusion Password Reset OTP",
            sender=app.config["MAIL_USERNAME"],
            recipients=[email]
        )

        msg.body = f"""
Hello {user.full_name},

Your password reset OTP is:

{otp}

This OTP will expire in 5 minutes.

If you did not request this, ignore this email.

FitFusion Team
"""

        mail.send(msg)

        return jsonify({"message": "OTP sent to email"})

    except Exception as e:

        print(e)
        return jsonify({"error": "Failed to send email"}), 500


# -----------------------------
# Verify OTP
# -----------------------------
@app.route("/verify-otp", methods=["POST"])
def verify_otp():

    data = request.get_json()

    email = data.get("email")
    otp = data.get("otp")

    if email not in otp_storage:
        return jsonify({"error": "OTP not requested"}), 400

    if time.time() - otp_time[email] > app.config["OTP_EXPIRE_TIME"]:
        del otp_storage[email]
        del otp_time[email]
        return jsonify({"error": "OTP expired"}), 400

    if otp_storage[email] != otp:
        return jsonify({"error": "Invalid OTP"}), 400

    del otp_storage[email]
    del otp_time[email]

    return jsonify({"message": "OTP verified"})

# -----------------------------
# Reset Password
# -----------------------------
@app.route("/reset-password", methods=["POST"])
def reset_password():

    data = request.get_json()

    email = data.get("email")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    hashed_password = bcrypt.hashpw(
        new_password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    user.password = hashed_password

    db.session.commit()

    return jsonify({"message": "Password reset successful"})

# -----------------------------
# Save / Update Activity
# -----------------------------
@app.route('/save_activity', methods=['POST'])
def save_activity():

    data = request.json

    user_id = data.get("user_id")
    steps = data.get("steps", 0)
    water = data.get("water_ml", 0)
    calories = data.get("calories", 0)

    today = date.today()

    activity = DailyActivity.query.filter_by(
        user_id=user_id,
        activity_date=today
    ).first()

    if activity:

        # update only if new values are higher
        if steps > activity.steps:
            activity.steps = steps

        if water > activity.water_ml:
            activity.water_ml = water

        if calories > activity.calories:
            activity.calories = calories

    else:

        activity = DailyActivity(
            user_id=user_id,
            steps=steps,
            water_ml=water,
            calories=calories,
            activity_date=today
        )

        db.session.add(activity)

    db.session.commit()

    return jsonify({"message": "Activity saved"})


# -----------------------------
# Get Today's Activity
# -----------------------------
@app.route('/get_today_activity/<int:user_id>', methods=['GET'])
def get_today_activity(user_id):

    today = date.today()

    activity = DailyActivity.query.filter_by(
        user_id=user_id,
        activity_date=today
    ).first()

    if activity:
        return jsonify({
            "steps": activity.steps,
            "water_ml": activity.water_ml,
            "calories": activity.calories
        })

    return jsonify({
        "steps": 0,
        "water_ml": 0,
        "calories": 0
    })


# -----------------------------
# Weekly Progress
# -----------------------------
@app.route('/weekly_progress/<int:user_id>', methods=['GET'])
def weekly_progress(user_id):

    activities = DailyActivity.query.filter_by(user_id=user_id)\
        .order_by(DailyActivity.activity_date.desc())\
        .limit(7).all()

    result = []

    for a in activities:
        result.append({
            "date": str(a.activity_date),
            "steps": a.steps,
            "water": a.water_ml,
            "calories": a.calories
        })

    return jsonify(result)


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)