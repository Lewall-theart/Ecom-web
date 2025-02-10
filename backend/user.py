from __main__ import app, db, encrypt_session_string, decrypt_session_string
from flask import request, jsonify
import bcrypt


@app.route("/get_info_from_session", methods=["GET"])
def get_info_from_session():
    try:
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Could not obtain session token in request."})

    if (encrypted_session_str == ""):
        return ({"status": "fail", "message": "Session token cannot be empty."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    cursor.execute("select id, name from Users where email = %s", (session_str[0],))
    account = cursor.fetchone()

    account_dict = {
        "id": account[0],
        "name": account[1],
        "email": session_str[0]
    }
    return jsonify({"status": "success", "message": "Got account information!", "account": account_dict})


@app.route("/user_edit_info", methods=["POST"])
def user_edit_info():
    try:
        account_id = request.json["id"]
        name = request.json["name"]
        email = request.json["email"]
        old_password = request.json.get("old_password", "")
        new_password = request.json.get("new_password", "")
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (account_id == "" or encrypted_session_str == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty (except for the password fields)."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    if not name or not email:
        return jsonify({"status": "fail", "message": "Name and email must not be empty!"})

    if not old_password:
        return jsonify({"status": "fail", "message": "Old password is required for editing."})

    cursor = db.cursor()

    cursor.execute("select * from Users where email = %s and password = %s and role = %s", (session_str[0], session_str[1], session_str[2]))
    valid_session_str = cursor.fetchone()
    if not valid_session_str:
        return jsonify({"status": "fail", "message": "Invalid user session."})

    cursor.execute("select * from Users where email = %s and not id = %s", (email, account_id))
    existing_account = cursor.fetchone()
    if existing_account:
        return jsonify({"status": "fail", "message": "Email is already associated with another account."})

    # verify old password first
    hashed_password = session_str[1]
    if new_password:
        print("has new password: " + new_password)
        cursor.execute("select password from Users where id = %s", (account_id,))
        stored_password = cursor.fetchone()[0]
        
        if not bcrypt.checkpw(old_password.encode(), stored_password.encode()):
            return jsonify({"status": "fail", "message": "Old password is incorrect."})
        
        # if old password is correct, hash new password
        hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        cursor.execute("update Users set name = %s, email = %s, password = %s where id = %s", (name, email, hashed_password, account_id))
    else:
        cursor.execute("select password from Users where id = %s", (account_id,))
        stored_password = cursor.fetchone()[0]
        
        if not bcrypt.checkpw(old_password.encode(), stored_password.encode()):
            return jsonify({"status": "fail", "message": "Old password is incorrect."})

        # no password change, just update name and email
        cursor.execute("update Users set name = %s, email = %s where id = %s", (name, email, account_id))

    db.commit()

    session_str = f"{email};{hashed_password};user"
    encrypted_session_str = encrypt_session_string(session_str)

    return jsonify({"status": "success", "message": "Account updated successfully!", "session_string": encrypted_session_str})


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    try:
        product_id = request.json["product_id"]
        account_id = request.json["user_id"]
        amount = request.json["amount"]
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (product_id == "" or account_id == "" or amount == "" or encrypted_session_str == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty."})

    try:
        int(amount)
    except:
        return ({"status": "fail", "message": "Amount must be an integer."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    cursor.execute("select id from Users where email = %s and password = %s and role = %s", (session_str[0], session_str[1], session_str[2]))
    valid_session_str = cursor.fetchone()

    if not valid_session_str:
        return jsonify({"status": "fail", "message": "Invalid user session."})

    if valid_session_str[0] != int(account_id):
        return jsonify({"status": "fail", "message": "User session doesn't match user request."})

    cursor.execute("select amount from Products where id = %s", (product_id,))
    stock_amount = cursor.fetchone()

    if not stock_amount:
        return jsonify({"status": "fail", "message": "Product not found."})

    cursor.execute("select id, amount from Cart where user_id = %s and product_id = %s", (account_id, product_id))
    cart_item = cursor.fetchone()

    new_amount = amount if not cart_item else cart_item[1] + amount

    if new_amount > stock_amount[0]:
        return jsonify({"status": "fail", "message": "Not enough products available."})
    
    if cart_item:
        # update the amount of the existing product in the cart
        cursor.execute("update Cart set amount = %s where id = %s", (new_amount, cart_item[0]))
    else:
        # insert a new product into the cart
        cursor.execute("insert into Cart (user_id, product_id, amount) values (%s, %s, %s)", (account_id, product_id, amount))

    db.commit()

    return jsonify({"status": "success", "message": "Product added to cart successfully!"})


@app.route("/get_cart", methods=["GET"])
def get_cart():
    try:
        user_id = request.args.get("id")
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (user_id == "" or encrypted_session_str == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    cursor.execute("select id from Users where email = %s and password = %s and role = %s", (session_str[0], session_str[1], session_str[2]))
    valid_session_str = cursor.fetchone()

    if not valid_session_str:
        return jsonify({"status": "fail", "message": "Invalid user session."})

    if valid_session_str[0] != int(user_id):
        return jsonify({"status": "fail", "message": "User session doesn't match user request."})

    cursor.execute("select product_id, name, price, Cart.amount from Cart join Products on Cart.product_id = Products.id where user_id = %s", (user_id,))
    products = cursor.fetchall()

    cart = []

    for product in products:
        product_dict = {
            "product_id": product[0],
            "name": product[1],
            "price": product[2],
            "amount": product[3]
        }
        cart.append(product_dict)

    if cart:
        return jsonify({"status": "success", "message": "Acquired products in cart.", "cart": cart})
    else:
        return jsonify({"status": "fail", "message": "Could not find any products in cart."})


@app.route("/del_product_from_cart", methods=["DELETE"])
def del_product_from_cart():
    try:
        user_id = request.args.get("user_id")
        product_id = request.args.get("product_id")
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (user_id == "" or product_id == "" or encrypted_session_str == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    cursor.execute("select id from Users where email = %s and password = %s and role = %s", (session_str[0], session_str[1], session_str[2]))
    valid_session_str = cursor.fetchone()

    if not valid_session_str:
        return jsonify({"status": "fail", "message": "Invalid user session."})

    if valid_session_str[0] != int(user_id):
        return jsonify({"status": "fail", "message": "User session doesn't match user request."})

    cursor.execute("delete from Cart where user_id = %s and product_id = %s", (user_id, product_id))
    db.commit()

    if cursor.rowcount > 0:
        return jsonify({"status": "success", "message": "Product successfully removed from cart."})
    else:
        return jsonify({"status": "fail", "message": "Product was not found and removed."})


@app.route("/update_product_in_cart", methods=["POST"])
def update_product_in_cart():
    try:
        user_id = request.json["user_id"]
        product_id = request.json["product_id"]
        amount = request.json["amount"]
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (user_id == "" or product_id == "" or amount == "" or encrypted_session_str == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    try:
        int(amount)
    except:
        return jsonify({"status": "success", "message": "Amount must be an integer."})

    cursor = db.cursor()

    cursor.execute("select id from Users where email = %s and password = %s and role = %s", (session_str[0], session_str[1], session_str[2]))
    valid_session_str = cursor.fetchone()

    if not valid_session_str:
        return jsonify({"status": "fail", "message": "Invalid user session."})

    if valid_session_str[0] != int(user_id):
        return jsonify({"status": "fail", "message": "User session doesn't match user request."})

    cursor.execute("select amount from Products where id = %s", (product_id,))
    stock_amount = cursor.fetchone()

    if not stock_amount:
        return jsonify({"status": "fail", "message": "Product not found."})

    if amount > stock_amount[0]:
        return jsonify({"status": "fail", "message": "Not enough products available.", "stock_amount": stock_amount[0]})

    cursor.execute("update Cart set amount = %s where user_id = %s and product_id = %s", (amount, user_id, product_id))
    db.commit()

    return jsonify({"status": "success", "message": "Product amount updated successfully!"})


@app.route("/get_cart_total", methods=["GET"])
def get_cart_total():
    try:
        user_id = request.args.get("user_id")
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (user_id == "" or encrypted_session_str == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty."})
        
    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    cursor.execute("select id from Users where email = %s and password = %s and role = %s", (session_str[0], session_str[1], session_str[2]))
    valid_session_str = cursor.fetchone()

    if not valid_session_str:
        return jsonify({"status": "fail", "message": "Invalid user session."})

    if valid_session_str[0] != int(user_id):
        return jsonify({"status": "fail", "message": "User session doesn't match user request."})

    cursor.execute("select Products.price, Cart.amount from Products join Cart on Products.id = Cart.product_id where Cart.user_id = %s", (user_id,))
    prices = cursor.fetchall()

    if prices:
        total = 0
        
        for price in prices:
            total += price[0] * price[1]

        return jsonify({"status": "success", "message": "Calculated total of user's cart.", "total": total})
    else:
        return jsonify({"status": "fail", "message": "Failed to fetch prices from products in cart."})


@app.route("/purchase_product", methods=["POST"])
def purchase_product():
    try:
        user_id = request.json["user_id"]
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (user_id == "" or encrypted_session_str == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    cursor.execute("select id from Users where email = %s and password = %s and role = %s", (session_str[0], session_str[1], session_str[2]))
    valid_session_str = cursor.fetchone()

    if not valid_session_str:
        return jsonify({"status": "fail", "message": "Invalid user session."})

    if valid_session_str[0] != int(user_id):
        return jsonify({"status": "fail", "message": "User session doesn't match user request."})

    cursor.execute("select product_id, amount from Cart where user_id = %s", (user_id,))
    products = cursor.fetchall()

    for product in products:
        cursor.execute("select amount from Products where id = %s", (product[0],))
        amount = cursor.fetchone()

        if (product[1] > amount[0]):
            return jsonify({"status": "fail", "message": "Not enough product for purchase."})

        cursor.execute("update Products set amount = %s where id = %s", (int(amount[0]) - int(product[1]), product[0]))
        db.commit()

    cursor.execute("delete from Cart where user_id = %s", (user_id,))
    db.commit()

    if cursor.rowcount > 0:
        return jsonify({"status": "success", "message": "Purchase products in cart successfully!"})
    else:
        return jsonify({"status": "fail", "message": "Could not find any products in cart."})
