from __main__ import app, db, decrypt_session_string
from flask import request, jsonify


@app.route("/get_products", methods=["GET"])
def get_products():
    cursor = db.cursor()

    cursor.execute("select * from Products")
    products = cursor.fetchall()

    # store result in a list of dictionaries
    product_list = []
    for product in products:
        product_dict = {
            "id": product[0],
            "name": product[1],
            "price": product[2],
            "amount": product[3],
            "description": product[4]
        }
        product_list.append(product_dict)

    return jsonify({"status": "success", "products": product_list})


@app.route("/get_product", methods=["GET"])
def get_product():
    try:
        product_id = request.args["id"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (product_id == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty."})

    cursor = db.cursor()

    cursor.execute("select * from Products where id = %s", (product_id,))
    product = cursor.fetchone()

    if product:
        product_dict = {
            "name": product[1],
            "price": product[2],
            "amount": product[3],
            "description": product[4]
        }
        return jsonify({"status": "success", "message": "Product found!", "product": product_dict})
    else:
        return jsonify({"status": "fail", "message": "Product not found!"})


@app.route("/create_product", methods=["POST"])
def create_product():
    try:
        name = request.json["name"]
        price = request.json["price"]
        amount = request.json["amount"]
        description = request.json["description"]
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (encrypted_session_str == ""):
        return ({"status": "fail", "message": "Session token cannot be empty."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    cursor.execute("select * from Users where email = %s and password = %s and role = 'admin'", (session_str[0], session_str[1]))
    is_admin = cursor.fetchone()
    if not is_admin:
        return jsonify({"status": "fail", "message": "Invalid session string, not an admin account"})

    if not name or not price or not amount or not description:
        return jsonify({"status": "fail", "message": "All fields must not be empty!"})

    try:
        float(price)
        int(amount)
    except:
        return jsonify({"status": "fail", "message": "Invalid data type for price and amount"})

    cursor.execute("select * from Products where name = %s", (name,))
    product = cursor.fetchone()
    
    if product:
        return jsonify({"status": "fail", "message": "Product already exists!"})
    else:
        cursor.execute("insert into Products (name, price, amount, description) values (%s, %s, %s, %s)", (name, price, amount, description))
        db.commit()
        return jsonify({"status": "success", "message": "Product created successfully!"})


@app.route("/edit_product", methods=["POST"])
def edit_product():
    try:
        prod_id = request.json["id"]
        name = request.json["name"]
        price = request.json["price"]
        amount = request.json["amount"]
        description = request.json["description"]
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})
        
    if (encrypted_session_str == ""):
        return ({"status": "fail", "message": "Session token cannot be empty."})
    
    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    cursor.execute("select * from Users where email = %s and password = %s and role = 'admin'", (session_str[0], session_str[1]))
    is_admin = cursor.fetchone()
    if not is_admin:
        return jsonify({"status": "fail", "message": "Invalid session string, not an admin account"})

    if not prod_id or not name or not price or not amount or not description:
        return jsonify({"status": "fail", "message": "All fields must not be empty!"})

    try:
        float(price)
        int(amount)
    except:
        return jsonify({"status": "fail", "message": "Invalid data type for price and amount"})

    cursor.execute("select * from Products where name = %s and not name = (select name from Products where id = %s)", (name, prod_id))
    existing_product = cursor.fetchone()

    if existing_product:
        return jsonify({"status": "fail", "message": "Product already exists."})
    else:
        cursor.execute("update Products set name = %s, price = %s, amount = %s, description = %s where id = %s", (name, price, amount, description, prod_id))
        db.commit()
        return jsonify({"status": "success", "message": "Product updated successfully!"})


@app.route("/delete_product", methods=["DELETE"])
def delete_product():
    try:
        product_id = request.args["id"]
        encrypted_session_str = request.headers["Auth-Token"]
    except:
        return ({"status": "fail", "message": "Invalid amount of variables in request."})

    if (product_id == "" or encrypted_session_str == ""):
        return ({"status": "fail", "message": "Variables in request cannot be empty."})

    session_str = decrypt_session_string(encrypted_session_str).split(";")

    cursor = db.cursor()

    cursor.execute("select * from Users where email = %s and password = %s and role = 'admin'", (session_str[0], session_str[1]))
    is_admin = cursor.fetchone()
    if not is_admin:
        return jsonify({"status": "fail", "message": "Invalid session string, not an admin account"})

    cursor.execute("delete from Products where id = %s", (product_id,))
    db.commit()

    # check if any row is deleted
    if cursor.rowcount > 0:
        return jsonify({"status": "success", "message": "Product deleted successfully!"})
    else:
        return jsonify({"status": "fail", "message": "Product not found!"})
