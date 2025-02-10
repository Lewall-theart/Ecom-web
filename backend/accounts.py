from __main__ import app, db, decrypt_session_string, encrypt_session_string
from flask import request, jsonify
import bcrypt


@app.route("/get_accounts", methods=["GET"])
def get_accounts():
    try:
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Could not obtain session token in request."})

    if (encrypted_session_str == ""):
        return ({"status": "fail", "message": "Session token cannot be empty."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    cursor.execute("select * from Users where email = %s and password = %s and role = 'admin'", (session_str[0], session_str[1]))
    is_admin = cursor.fetchone()
    if not is_admin:
        return jsonify({"status": "fail", "message": "Invalid session string, not an admin account"})

    cursor.execute("select * from Users")
    accounts = cursor.fetchall()

    account_list = []
    for account in accounts:
        account_dict = {
            "id": account[0],
            "name": account[1],
            "email": account[2],
            "password": "*****",
            "role": account[4]
        }
        account_list.append(account_dict)

    return jsonify({"status": "success", "accounts": account_list})


@app.route("/get_account", methods=["GET"])
def get_account():
    try:
        account_id = request.args["id"]
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (account_id == "" or encrypted_session_str == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty."})
    
    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    cursor.execute("select * from Users where email = %s and password = %s and role = 'admin'", (session_str[0], session_str[1]))
    is_admin = cursor.fetchone()
    if not is_admin:
        return jsonify({"status": "fail", "message": "Invalid session string, not an admin account"})

    cursor.execute("select * from Users where id = %s", (account_id,))
    account = cursor.fetchone()

    if account:
        account_dict = {
            "name": account[1],
            "email": account[2],
            "role": account[4]
        }
        return jsonify({"status": "success", "message": "Account found!", "account": account_dict})
    else:
        return jsonify({"status": "fail", "message": "Account not found!"})


@app.route("/create_account", methods=["POST"])
def create_account():
    try:
        name = request.json["name"]
        email = request.json["email"]
        password = request.json["password"]
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (encrypted_session_str == ""):
        return ({"status": "fail", "message": "Session token cannot be empty."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    if not name or not email or not password:
        return jsonify({"status": "fail", "message": "All fields must not be empty!"})

    cursor = db.cursor()

    cursor.execute("select * from Users where email = %s and password = %s and role = 'admin'", (session_str[0], session_str[1]))
    is_admin = cursor.fetchone()
    if not is_admin:
        return jsonify({"status": "fail", "message": "Invalid session string, not an admin account"})

    cursor.execute("select * from Users where email = %s", (email,))
    existing_account = cursor.fetchone()
    
    if existing_account:
        return jsonify({"status": "fail", "message": "Account already exists!"})
    else:
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        cursor.execute("insert into Users (name, email, password, role) values (%s, %s, %s, %s)", (name, email, hashed_password.decode(), "user"))
        db.commit()
        return jsonify({"status": "success", "message": "Account created successfully!"})


@app.route("/edit_account", methods=["POST"])
def edit_account():
    try:
        account_id = request.json["id"]
        name = request.json["name"]
        email = request.json["email"]
        password = request.json["password"]
        old_password = request.json.get("old_password", "")
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (account_id == "" or encrypted_session_str == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty (except for the password fields)."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    if not name or not email:
        return jsonify({"status": "fail", "message": "Name and email must not be empty!"})

    cursor = db.cursor()

    cursor.execute("select * from Users where email = %s and password = %s and role = 'admin'", (session_str[0], session_str[1]))
    is_admin = cursor.fetchone()
    if not is_admin:
        return jsonify({"status": "fail", "message": "Invalid session string, not an admin account"})

    cursor.execute("select password, role from Users where id = %s", (account_id,))
    account = cursor.fetchone()

    if account[1] == "admin" and old_password:
        if not bcrypt.checkpw(old_password.encode(), account[0].encode()):
            return jsonify({"status": "fail", "message": "Old password is incorrect."})
    elif account[1] == "admin" and not old_password:
        return jsonify({"status": "fail", "message": "Editing admin password requires old password."})

    cursor.execute("select * from Users where email = %s and not email = (select email from Users where id = %s)", (email, account_id))
    existing_account = cursor.fetchone()

    if existing_account:
        return jsonify({"status": "fail", "message": "Email is already associated with another account."})
    else:
        session_str = ""

        if password == "":
            cursor.execute("update Users set name = %s, email = %s where id = %s", (name, email, account_id))
            db.commit()

            if account[1] == "admin":
                cursor.execute("select password, role from Users where role = admin")
                result = cursor.fetchone()
                session_str = f"{email};{result[0]};{result[1]}"
        else:
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            cursor.execute("update Users set name = %s, email = %s, password = %s where id = %s", (name, email, hashed_password.decode(), account_id))
            db.commit()
            
            if account[1] == "admin":
                session_str = f"{email};{hashed_password.decode()};{account[1]}"

        if account[1] == "admin":
            return jsonify({"status": "success", "message": "Updated admin account information!", "session_string": encrypt_session_string(session_str)})

        return jsonify({"status": "success", "message": "Account updated successfully!"})


@app.route("/delete_account", methods=["DELETE"])
def delete_account():
    try:
        account_id = request.args["id"]
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (account_id == "" or encrypted_session_str == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    cursor.execute("select * from Users where email = %s and password = %s and role = 'admin'", (session_str[0], session_str[1]))
    is_admin = cursor.fetchone()
    if not is_admin:
        return jsonify({"status": "fail", "message": "Invalid session string, not an admin account"})

    cursor.execute("delete from Users where id = %s", (account_id,))
    db.commit()

    # check if any row is deleted
    if cursor.rowcount > 0:
        return jsonify({"status": "success", "message": "Account deleted successfully!"})
    else:
        return jsonify({"status": "fail", "message": "Account not found!"})
