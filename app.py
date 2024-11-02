import os
from flask import Flask, redirect, url_for, render_template, request, jsonify, session, flash
import boto3
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')  # Load secret key from environment variable

# Initialize the S3 client without hardcoded credentials
s3_client = boto3.client(
    "s3",
)


# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://mist2_database_user:coNqWZsznpcEKYWQgWF2pam5UnSvjzUT@dpg-csj9uae8ii6s73d1tdt0-a.ohio-postgres.render.com/mist2_database"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = 'you-will-never-guess1315123'  # Replace with a secure key

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Route for home page
@app.route("/")
def index():
    return render_template("updatedHomePage.html")

# Route for sign-upt
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
            flash("Logged in successfully!")
            return redirect(url_for("homepage"))
        else:
            flash("Invalid username or password. Please try again.")
            return redirect(url_for("index"))

    return render_template("login.html")

# Route for logout
@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Logged out successfully.")
    return redirect(url_for("home"))


migrate = Migrate(app, db)


# Route for user sign-in


# Route for the homepage
@app.route('/homepage', methods=['GET', 'POST'])
def homepage():
    return render_template('homepage.html')

# Route for submitting data
@app.route('/submit', methods=['POST'])
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

# Route for clearing specific data
@app.route('/clear/<engine_name>', methods=['DELETE'])
def clear_specific_data(engine_name):
    file_name = f"{engine_name}.json"
    
    try:
        # Delete the specific data from S3
        s3_client.delete_object(Bucket=os.environ.get('BUCKET_NAME', 'hacknjitdata'), Key=file_name)
        return jsonify({"message": "Data cleared successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error clearing data: {str(e)}"}), 500

# Route for clearing all data
@app.route('/clear/all', methods=['DELETE'])
def clear_all_data():
    try:
        # List objects in the bucket and delete them
        response = s3_client.list_objects_v2(Bucket=os.environ.get('BUCKET_NAME', 'hacknjitdata'))
        
        if 'Contents' in response:
            for obj in response['Contents']:
                s3_client.delete_object(Bucket=os.environ.get('BUCKET_NAME', 'hacknjitdata'), Key=obj['Key'])
        
        return jsonify({"message": "All data cleared successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error clearing all data: {str(e)}"}), 500

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run()
