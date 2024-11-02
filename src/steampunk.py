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

# Steampunk colors and font
BACKGROUND_COLOR = "#3b2f2f"  # Dark brass background
BUTTON_COLOR = "#d3a625"  # Brass button color
FONT_COLOR = "#ffecb3"  # Light, faded yellow for text
FONT = ("Old English", 12, "bold")  # Adjust to your preferred steampunk font

# Function to upload or update data to S3
def upload_data_to_s3(bucket_name, user_id, account_data):
    try:
        file_name = f"user_data/{user_id}.json"
        
        try:
            response = s3.get_object(Bucket=bucket_name, Key=file_name)
            existing_data = json.loads(response['Body'].read())
        except ClientError as e:
            if e.response['Error']['Code'] == "NoSuchKey":
                existing_data = []
            else:
                print("Error retrieving existing data:", e)
                return
        
        account_data['Timestamp'] = datetime.now(timezone.utc).isoformat()
        updated = False

        for existing_account in existing_data:
            if existing_account['Website/App'] == account_data['Website/App']:
                existing_account.update(account_data)
                updated = True
                break
        
        if not updated:
            existing_data.append(account_data)

        json_data = json.dumps(existing_data)
        
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
    file_name = f"user_data/{user_id}.json"
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_name)
        data = json.loads(response['Body'].read())
        return data
    except ClientError as e:
        if e.response['Error']['Code'] == "NoSuchKey":
            return None
        else:
            print("Error retrieving data:", e)
            return None

# Function to clear all data in the bucket
def clear_bucket_data(bucket_name):
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
                print(f"Deleted: {obj['Key']}")
            print("All data cleared from the bucket.")
        else:
            print("No objects found in the bucket.")
    except ClientError as e:
        print("Error clearing bucket data:", e)

# Function to show message box with steampunk styling
def show_message(message):
    messagebox.showinfo("Information", message)

# Function to get user input with steampunk styling
def get_user_input(title, prompt, default_value=None):
    while True:
        input_value = simpledialog.askstring(title, prompt, initialvalue=default_value, parent=root)
        if input_value is None:
            return None
        elif input_value.strip() == "":
            show_message("Error: Input cannot be empty. Please enter a value.")
        else:
            return input_value

# Function to handle the upload process through the UI
def handle_upload():
    user_id = get_user_input("User ID", "Enter User ID (You Will Need Your ID To Get Your Account Information):")
    if user_id is None:
        return

    website_app = get_user_input("Website/App", "Enter The Website/App:")
    if website_app is None:
        return

    password = get_user_input("Password", "Enter The Password:")
    if password is None:
        return

    username = get_user_input("Username", "Enter The Username:")
    if username is None:
        return

    email = get_user_input("Email", "Enter The Email:")
    if email is None:
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
    if user_id is None:
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

# Function to create the main application window
def create_main_window():
    global bucket_name
    bucket_name = 'hacknjitdata'  # Replace with your actual bucket name

    global root
    root = tk.Tk()
    root.title("Steampunk Account Manager")
    root.geometry("475x275")
    root.configure(bg=BACKGROUND_COLOR)
    center_window(root)

    welcome_label = tk.Label(root, text="Welcome to the Steampunk Account Manager", font=FONT, fg=FONT_COLOR, bg=BACKGROUND_COLOR, wraplength=350, justify="center")
    welcome_label.pack(pady=20)

    enter_button = tk.Button(root, text="Enter", command=launch_main_app, font=FONT, bg=BUTTON_COLOR, fg=FONT_COLOR, relief="ridge", borderwidth=3)
    enter_button.pack(pady=10)

    root.mainloop()

# Function to launch the main application window
def launch_main_app():
    root.destroy()
    create_application_window()

# Function to create the main application window
def create_application_window():
    global root
    root = tk.Tk()
    root.title("Steampunk Account Manager")
    root.geometry("300x250")
    root.configure(bg=BACKGROUND_COLOR)
    center_window(root)

    tk.Label(root, text="Account Manager Options", font=FONT, fg=FONT_COLOR, bg=BACKGROUND_COLOR).pack(pady=10)

    buttons = {
        "Store Account Info": handle_upload,
        "Get Account Info": handle_retrieve,
    }

    for label, command in buttons.items():
        button = tk.Button(root, text=label, command=command, font=FONT, bg=BUTTON_COLOR, fg=FONT_COLOR, relief="raised", borderwidth=3)
        button.pack(pady=5)

    root.mainloop()

# Function to center the window
def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

if __name__ == "__main__":
    create_main_window()
