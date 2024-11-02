import os
from flask import Flask, redirect, url_for, render_template, request, jsonify, session
import boto3
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')  # Load secret key from environment variable

# Initialize the S3 client without hardcoded credentials
s3_client = boto3.client(
    "s3", #-1 Specify your AWS region
)
# In-memory user storage (for demonstration purposes)
users = {}

# Route for the sign-in page
@app.route("/")
def signin():
    success_message = request.args.get('success')
    return render_template("realhomepage.html", success_message=success_message)

# Route for creating a new account
@app.route('/createAccount', methods=['GET', 'POST'])
def createAccount():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate input
        if not username or not password:
            return jsonify({"message": "Username and password are required."}), 400  # Bad request

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Check if the username already exists
        if username in users:
            return jsonify({"message": "Username already exists. Please choose a different one."}), 400  # Bad request

        # Store the user data
        users[username] = hashed_password
        
        # Return a success response with the homepage URL
        return jsonify({"url": url_for('homepage')}), 200  # Change to JSON response

    return render_template('homepage.html')

# Route for user sign-in
# Route for user sign-in
@app.route('/signIn', methods=['GET', 'POST'])
def signIn():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user exists and password matches
        if username in users and check_password_hash(users[username], password):
            session['username'] = username  # Store username in session
            return redirect(url_for('homepage'))  # Redirect to the homepage
        else:
            # Return an error message if sign-in fails
            error_message = "Invalid username or password. Please try again."
            return render_template('updatedHomePage.html', error_message=error_message)

    return render_template('updatedHomePage.html')


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
    app.run(debug=True)
