import boto3
import json
from botocore.exceptions import ClientError
from datetime import datetime, timezone
import tkinter as tk
from tkinter import messagebox, simpledialog

# Initialize the S3 client
s3 = boto3.client('s3', region_name='us-west-2')

# Developer/Admin key
ADMIN_KEY = 'sZco=Tsh:zoZPJS'

# Function to upload or update data to S3
def upload_data_to_s3(bucket_name, user_id, account_data):
    try:
        file_name = f"user_data/{user_id}.json"  # Path to the user's JSON file
        
        # Attempt to retrieve existing data
        try:
            response = s3.get_object(Bucket=bucket_name, Key=file_name)
            existing_data = json.loads(response['Body'].read())
        except ClientError as e:
            if e.response['Error']['Code'] == "NoSuchKey":
                existing_data = []  # If no existing data, start with an empty list
            else:
                print("Error retrieving existing data:", e)
                return
        
        # Prepare to update or append account data
        account_data['Timestamp'] = datetime.now(timezone.utc).isoformat()  # Correct timestamp
        updated = False

        # Check if the account already exists in the existing data
        for existing_account in existing_data:
            if existing_account['Website/App'] == account_data['Website/App']:
                existing_account.update(account_data)  # Update existing account data
                updated = True
                break
        
        if not updated:
            existing_data.append(account_data)  # Append if not found

        # Convert the updated data to JSON format
        json_data = json.dumps(existing_data)
        
        # Upload the updated data to S3
        s3.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=json_data,
            ContentType='application/json'
        )
        print("Data Successfully Saved.")
    except ClientError as e:
        print("Error uploading data:", e)

# Function to retrieve user data from S3
def retrieve_user_data(bucket_name, user_id):
    file_name = f"user_data/{user_id}.json"  # Path to the user's JSON file
    try:
        # Fetch the object from S3
        response = s3.get_object(Bucket=bucket_name, Key=file_name)
        
        # Read the content and parse it as JSON
        data = json.loads(response['Body'].read())
        return data  # Return data for further processing
    except ClientError as e:
        if e.response['Error']['Code'] == "NoSuchKey":
            return None  # No data found for the given User ID
        else:
            print("Error retrieving data:", e)
            return None

# Function to clear all data in the bucket
def clear_bucket_data(bucket_name):
    try:
        # List objects in the bucket
        response = s3.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                # Delete each object
                s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
                print(f"Deleted: {obj['Key']}")
            print("All data cleared from the bucket.")
        else:
            print("No objects found in the bucket.")
    except ClientError as e:
        print("Error clearing bucket data:", e)

# Function to show message box
def show_message(message):
    messagebox.showinfo("Information", message)

# Function to get user input with centering and topmost attribute
def get_user_input(title, prompt, default_value=None):
    while True:  # Loop until valid input is received
        input_value = simpledialog.askstring(title, prompt, initialvalue=default_value, parent=root)  # Use parent=root to keep it on top
        if input_value is None:  # User canceled
            return None
        elif input_value.strip() == "":  # Check if the input is empty
            show_message("Error: Input cannot be empty. Please enter a value.")
        else:
            return input_value

# Function to handle the upload process through the UI
def handle_upload():
    user_id = get_user_input("User ID", "Enter User ID (You Will Need Your ID To Get Your Account Information):")
    if user_id is None:  # Check if canceled
        return

    website_app = get_user_input("Website/App", "Enter The Website/App:")
    if website_app is None:  # Check if canceled
        return

    password = get_user_input("Password", "Enter The Password:")
    if password is None:  # Check if canceled
        return

    username = get_user_input("Username", "Enter The Username:")
    if username is None:  # Check if canceled
        return

    email = get_user_input("Email", "Enter The Email:")
    if email is None:  # Check if canceled
        return

    account_data = {
        'Website/App': website_app,
        'Password': password,
        'Username': username,
        'Email': email,
    }
    upload_data_to_s3(bucket_name, user_id, account_data)
    show_message("Data successfully uploaded.")

# Function to handle the retrieve process through the UI
def handle_retrieve():
    user_id = get_user_input("User ID", "Enter User ID to retrieve data:")
    if user_id is None:  # Check if canceled
        return

    data = retrieve_user_data(bucket_name, user_id)
    if data is None:
        show_message("No data found for the given User ID.")
    else:
        retrieved_info = ""
        for account in data:
            retrieved_info += (
                f"Website/App: {account.get('Website/App', 'N/A')}\n"
                f"Username: {account.get('Username', 'N/A')}\n"
                f"Password: {account.get('Password', 'N/A')}\n"
                f"Email: {account.get('Email', 'N/A')}\n"
                f"Timestamp: {account.get('Timestamp', 'N/A')}\n"
                "----------\n"
            )
        show_message(retrieved_info)

# Function to handle updating account information
def handle_update():
    user_id = get_user_input("User ID", "Enter User ID to update data:")
    if user_id is None:  # Check if canceled
        return

    data = retrieve_user_data(bucket_name, user_id)
    if data is None:
        show_message("No data found for the given User ID.")
        return

    website_app = get_user_input("Website/App", "Enter Website/App to update:")
    if website_app is None:  # Check if canceled
        return

    existing_account = next((account for account in data if account['Website/App'] == website_app), None)
    if not existing_account:
        show_message("No account found for the given Website/App.")
        return

    # Get new values for updating
    password = get_user_input("Password", "Enter new Password:", existing_account['Password'])
    if password is None:
        return
    username = get_user_input("Username", "Enter new Username:", existing_account['Username'])
    if username is None:
        return
    email = get_user_input("Email", "Enter new Email:", existing_account['Email'])
    if email is None:
        return

    # Prepare updated data
    updated_data = {
        'Website/App': website_app,
        'Password': password,
        'Username': username,
        'Email': email,
    }

    # Call upload_data_to_s3 to save the updated account information
    upload_data_to_s3(bucket_name, user_id, updated_data)  # Ensure we're using the correct user_id
    show_message("Account information updated successfully.")

# Function to handle clearing the bucket through the UI
def handle_clear():
    admin_key = get_user_input("Admin Key", "Enter the developer/admin key to proceed with clearing the bucket:")
    if admin_key == ADMIN_KEY:
        confirm = get_user_input("Confirm", "Are you sure you want to clear all data from the bucket? Type 'yes' to confirm:")
        if confirm and confirm.lower() == 'yes':
            clear_bucket_data(bucket_name)
            show_message("All data cleared from the bucket.")
        else:
            show_message("Clear operation canceled.")
    else:
        show_message("Invalid Admin Key. Clear operation aborted.")

# Function to create the main application window
def create_main_window():
    global bucket_name
    bucket_name = 'hacknjitdata'  # Replace with your actual bucket name

    # Create the main Tkinter window
    global root  # Make root global to use in other functions
    root = tk.Tk()
    root.title("Welcome to Account Manager")
    root.geometry("475x275")  # Set the window size
    center_window(root)

    # Add a welcome message and description
    welcome_label = tk.Label(root, text="Welcome to the Account Manager App Read Below For A Quick Tutorial!\n\nThis app allows you to securely store,\n and manage all of your passwords and account information.\n\n Click Store: To store account information \n Click Get: To retrieve account information \n Click Update: To change account information for an app/website \n\n\n Press Enter To Access The Application", wraplength=350, justify="center")
    welcome_label.pack(pady=20)

    # Create the Enter button to proceed to the main application
    enter_button = tk.Button(root, text="Enter", command=launch_main_app)
    enter_button.pack(pady=10)

    # Start the Tkinter main loop
    root.mainloop()

# Function to launch the main application window
def launch_main_app():
    root.destroy()  # Close the welcome window
    create_application_window()  # Call to create the main application window

# Function to create the main application window
def create_application_window():
    global root  # Use the existing root variable
    root = tk.Tk()
    root.title("Account Manager")
    root.geometry("300x190")  # Set the window size
    center_window(root)

    # Create buttons for actions
    upload_button = tk.Button(root, text="Store Account Info", command=handle_upload)
    upload_button.pack(pady=5)

    retrieve_button = tk.Button(root, text="Get Account Info", command=handle_retrieve)
    retrieve_button.pack(pady=5)

    update_button = tk.Button(root, text="Update Account Info", command=handle_update)
    update_button.pack(pady=5)

    clear_button = tk.Button(root, text="Clear All Data", command=handle_clear)
    clear_button.pack(pady=5)

    # Start the Tkinter main loop
    root.mainloop()

# Function to center the window
def center_window(window):
    window.update_idletasks()  # Update "requested size" from geometry manager
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

# Run the main application
if __name__ == "__main__":
    create_main_window()
