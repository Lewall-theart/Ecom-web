from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_wtf import CSRFProtect
from dotenv import load_dotenv
import MySQLdb
import bcrypt
import os
import rsa
import base64


load_dotenv()
app = Flask(__name__)

allowed_origins = [
    "http://127.0.0.1:5500"
]

CORS(app, origins=allowed_origins)
public_key, private_key = rsa.newkeys(1024)


# connect to mysql
db = MySQLdb.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    passwd=os.getenv("MYSQL_PASSWORD"),
    db=os.getenv("MYSQL_DB")
)


def encrypt_session_string(data):
    encrypted_data = rsa.encrypt(data.encode(), public_key)
    return base64.b64encode(encrypted_data).decode() # decode since b64encode returns byte string


def decrypt_session_string(data):
    encrypted_data = base64.b64decode(data.encode())
    return rsa.decrypt(encrypted_data, private_key).decode()


# import endpoints from other files
import products
import accounts
import user


# endpoint for login
@app.route("/login", methods=["POST"])
def login():
    try:
        email = request.json["email"]
        password = request.json["password"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (email == "" or password == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty."})

    # get the password of email from db
    cursor = db.cursor()
    cursor.execute("select password, role from Users where email = %s", (email,))
    result = cursor.fetchone()

    # compare password with given password (with hashing)
    if result:
        hashed_password = result[0].encode()
        
        if bcrypt.checkpw(password.encode(), hashed_password):
            session_str = f"{email};{result[0]};{result[1]}"
            encrypted_session_str = encrypt_session_string(session_str)

            return jsonify({"status": "success", "message": "Login successful!", "session_string": encrypted_session_str, "role": result[1]})
        else:
            return jsonify({"status": "fail", "message": "Invalid credentials!"})
    else:
        return jsonify({"status": "fail", "message": "Invalid credentials!"})


# endpoint for registration
@app.route("/register", methods=["POST"])
def register():
    try:
        name = request.json["name"]
        email = request.json["email"]
        password = request.json["password"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (name == "" or email == "" or password == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty."})

    cursor = db.cursor()

    # check if email already exists
    cursor.execute("select * from Users where email = %s", (email,))
    email_exists = cursor.fetchone()
    if email_exists:
        return jsonify({"status": "fail", "message": "Email already exists!"})

    # hash password
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    # insert data into db
    cursor.execute("insert into Users (name, email, password, role) values (%s, %s, %s, %s)", (name, email, hashed_password.decode(), "user"))
    db.commit()
    return jsonify({"status": "success", "message": "Registration successful!"})


# endpoint for session string validation
@app.route("/validate_session", methods=["POST"])
def validate_session():
    try:
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Could not obtain session token in request."})

    if (encrypted_session_str == ""):
        return ({"status": "fail", "message": "Session token cannot be empty."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    # check if session information is valid
    cursor.execute("select * from Users where email = %s and password = %s and role = %s", (session_str[0], session_str[1], session_str[2]))
    valid_user = cursor.fetchone()
    if valid_user:
        return jsonify({"status": "success", "message": "Valid session string.", "role": session_str[2]})

    return jsonify({"status": "fail", "message": "Invalid session string."})


if __name__ == "__main__":
    app.run(debug=True)
