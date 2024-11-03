import os
from flask import Flask, redirect, url_for, render_template, request, jsonify, session, flash
import boto3
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
from functools import wraps  # Import for decorator
from flask_login import login_required, login_user, LoginManager

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')

# Initialize the S3 client without hardcoded credentials
s3_client = boto3.client("s3")

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://mist2_database_user:coNqWZsznpcEKYWQgWF2pam5UnSvjzUT@dpg-csj9uae8ii6s73d1tdt0-a.ohio-postgres.render.com/mist2_database"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = 'you-will-never-guess1315123'  # Ensure this is secure in production

# Initialize SQLAlchemy
db = SQLAlchemy(app)

login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view='index'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return True  # All users are active

    @property
    def is_authenticated(self):
        return True  # This user is authenticated

    @property
    def is_anonymous(self):
        return False  # This user is not anonymous

    def get_id(self):
        return str(self.id)  # Flask-Login expects the user_id to be a string

# Routes

@app.route('/systemmanager')
@login_required
def systemManager():
    return render_template('systemmanager.html')


@app.route("/")
def index():
    return render_template("updatedHomePage.html")

@app.route("/contact")
@login_required
def contact():
    return render_template("contact.html")

@app.route("/comingsoon")
@login_required
def comingsoon():
    return render_template("comingsoon.html")

@app.route("/csettings")
@login_required
def settings():
    return render_template("settings.html")

# Route for sign-up
@app.route("/createAccount", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose a different one.")
            return redirect(url_for("signup"))

        # Create a new user
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully. Please log in.")
        return redirect(url_for("index"))

    return render_template("updatedHomePage.html")

# Route for login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if user exists and password is correct
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["username"] = username
            login_user(user)
            flash("Logged in successfully!")
            return redirect(url_for("homepage"))
        else:
            flash("Invalid username or password. Please try again.")
            return redirect(url_for("index"))

    return render_template("login.html")

# Route for logout
@app.route("/logout")
@login_required
def logout():
    session.pop("username", None)
    flash("Logged out successfully.")
    return redirect(url_for("index"))

migrate = Migrate(app, db)

# Route for the homepage
@app.route('/homepage', methods=['GET', 'POST'])
@login_required
def homepage():
    return render_template('homepage.html')

# Route for submitting data
@app.route('/submit', methods=['POST'])
@login_required
def submit_data():
    data = request.json
    file_name = f"{data['engineName']}.json"
    
    # Validate required fields
    if not data.get('engineName') or not data.get('submissionDate'):
        return jsonify({"message": "System Name and Submission Date are required."}), 400

    try:
        # Save data to S3
        s3_client.put_object(
            Bucket=os.environ.get('BUCKET_NAME', 'hacknjitdata'),  # Get bucket name from environment variable
            Key=file_name,
            Body=json.dumps(data),
            ContentType='application/json'
        )
        return jsonify({"message": "Data submitted successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error submitting data: {str(e)}"}), 500

# Route for retrieving data
@app.route('/retrieve/<engine_name>', methods=['GET'])
@login_required
def retrieve_data(engine_name):
    file_name = f"{engine_name}.json"
    
    try:
        # Retrieve data from S3
        response = s3_client.get_object(Bucket=os.environ.get('BUCKET_NAME', 'hacknjitdata'), Key=file_name)
        data = json.loads(response['Body'].read().decode('utf-8'))
        return jsonify({"data": data})
    except s3_client.exceptions.NoSuchKey:
        return jsonify({"message": f"No data found for {engine_name}."}), 404
    except Exception as e:
        return jsonify({"message": f"Error retrieving data: {str(e)}"}), 500

# Route for sorting retrieved data
@app.route('/retrieve/sorted', methods=['GET'])
@login_required
def retrieve_sorted_data():
    sort_by = request.args.get('sort_by')
    bucket_name = os.environ.get('BUCKET_NAME', 'hacknjitdata')
    
    try:
        # List all objects in the bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        all_data = []

        if 'Contents' in response:
            for obj in response['Contents']:
                file_name = obj['Key']
                
                # Get the data from each file
                response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
                data = json.loads(response['Body'].read().decode('utf-8'))
                
                data['weight'] = float(data['weight'])  # Ensure weight is a float
                data['submissionDate'] = data['submissionDate']  # Keep the date as a string
                data['engineName'] = data['engineName']  # Ensure we have the name
                
                all_data.append(data)

        # Sort data based on the specified sort_by criteria
        if sort_by == 'date':
            sorted_data = sorted(all_data, key=lambda x: x['submissionDate'], reverse=True)
        elif sort_by == 'weight':
            sorted_data = sorted(all_data, key=lambda x: x['weight'], reverse=True)
        elif sort_by == 'name':
            sorted_data = sorted(all_data, key=lambda x: x['engineName'].lower())  # Sort alphabetically
        else:
            return jsonify({"message": "Invalid sort parameter."}), 400

        return jsonify({"data": sorted_data})
        
    except Exception as e:
        return jsonify({"message": f"Error retrieving sorted data: {str(e)}"}), 500

# Route for predicting failure
@app.route('/predict/failure', methods=['GET'])
@login_required
def predict_failure():
    system_name = request.args.get('system_name')
    file_name = f"{system_name}.json"
    
    try:
        # Retrieve the specific engine data from S3
        response = s3_client.get_object(Bucket=os.environ.get('BUCKET_NAME', 'hacknjitdata'), Key=file_name)
        data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Example prediction logic: add 30 days to the submission date
        submission_date = datetime.strptime(data['submissionDate'], "%Y-%m-%d")
        predicted_failure_date = submission_date + timedelta(days=30)
        
        return jsonify({"predictedFailureDate": predicted_failure_date.strftime("%Y-%m-%d")})
    except s3_client.exceptions.NoSuchKey:
        return jsonify({"message": f"No data found for {system_name}."}), 404
    except Exception as e:
        return jsonify({"message": f"Error predicting failure: {str(e)}"}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
