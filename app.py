import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd, mxn_currency
import datetime
import json  # Import the json module


 

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.autoescape = True  # Optional security measure 
app.jinja_env.filters["mxn"] = mxn_currency


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///lasocial.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    name = request.args.get("name", "world")
    return render_template("index.html", name=name)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():

    #Clear out any previous user sessions
    session.clear()

    """Register user"""

    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        #Check for Username
        if not username:
            return apology("Username is a Requiered Field",400)
        #Check for Password
        if not password:
            return apology("Password is a Requiered Field",400)
        #Check for Password Confirmation
        if not confirmation:
            return apology("Password Confirmation is Requiered",400)
        #Check if password=confirmation are equal
        if password != confirmation:
            return apology("Confirmation and Password Do Not Match!",400)

    #Hash - Cypher Password
    hash = generate_password_hash(password)

    #Query Datebase to see if username already exists
    rows = db.execute("SELECT * FROM users WHERE username = ?",username)

    if len(rows) != 0:
        return apology("Username Exists in our Database",400)

    # Register User
    db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)

    return redirect("/success")

@app.route("/insights", methods=["GET", "POST"])
@login_required
def insights():
    """Show Products"""
    gls_db = db.execute("SELECT gl_description, count(lssin) AS product_count, ROUND(CAST(count(lssin) AS FLOAT) / (SELECT SUM(product_count) FROM (SELECT gl_description, count(lssin) AS product_count FROM lssin GROUP BY gl_description) AS total_count_table), 4) *100 AS share_of_total FROM lssin GROUP BY gl_description ORDER BY share_of_total DESC")
    return render_template("insights.html", products = gls_db)

@app.route("/products", methods=["GET", "POST"])
@login_required
def products():
    """Show Products"""
   
    if request.method == "GET":
        lssin_db = db.execute("SELECT LSSIN, brand_name, gl_description, item_name, image, msrp_tax_amount, category_name, subcategory_name from lssin order by brand_name")
        lssin_cursor = db.execute("SELECT * from lssin")
        lssin_count = len(lssin_cursor)  # Use len() to get the count of rows (list items)
        print("lssin_count:", lssin_count)  # Add this print statement
        return render_template("products.html", products=lssin_db, lssin_count=lssin_count)
    
    elif request.method == "POST":
        print("Form data:", request.form)  # Add this print statement
        LSSIN = request.form.get("LSSIN")
        print("lssin:", LSSIN)  # Add this print statement
        if LSSIN:
            #return render_template("product_page.html", lssin=lssin)  # Redirect to products_page.html with lssin
            return redirect(f"product_page/{LSSIN}")
        else:
            print("No lssin found in form data")  # Add this print statement
            return "No lssin provided"
    else:
        return "Invalid form submission"


@app.route("/product_page/<LSSIN>", methods=["GET", "POST"])
@login_required
def product_page(LSSIN):
    """Displays specific product details based on lssin."""
    
    # Fetch product details from your database using lssin
    
    if request.method == "GET":
        product_details = db.execute("SELECT * FROM lssin WHERE lssin = ?", (LSSIN,))  # Assuming lssin is a unique identifier
        print("product_details:", product_details)  # Add this print statement
        print("lssin:", LSSIN)  # Add this print statement

    # Check if product is found
        if product_details:
            product = product_details[0]  # Get the first row as a dictionary
            return render_template("product_page.html", product=product)
        else:
            return "Product not found"  # Handle case where product doesn't exist

    elif request.method == "POST":
        LSSIN = request.form.get("LSSIN")
        print("lssin:", LSSIN)  # Add this print statement
        if LSSIN:
            #return render_template("product_page.html", lssin=lssin)  # Redirect to products_page.html with lssin
            return redirect(f"edit_product/{LSSIN}")
        else:
            print("No lssin found in form data")  # Add this print statement
            return "No lssin provided"
    else:
        return "Invalid form submission"


@app.route("/edit_product/<LSSIN>", methods=["GET", "POST"])
@login_required
def edit_product(LSSIN):
    """Edit product details based on lssin."""
    
    # Fetch product details from your database using lssin
    product_details = db.execute("SELECT * FROM lssin WHERE lssin = ?", (LSSIN,))

    gl_description_options = db.execute("SELECT distinct gl_description FROM gl_product_group")
    gl_description_values = [option['gl_description'] for option in gl_description_options]
    gl_description_values_json = json.dumps(gl_description_values) # Serialize gl_description_values to a JSON string

    category_name_option = db.execute("SELECT distinct category_name FROM categories")
    category_name_values = [option['category_name'] for option in category_name_option]
    category_name_values_json = json.dumps(category_name_values)

    subcategory_name_option = db.execute("SELECT distinct subcategory_name FROM subcategories")
    subcategory_name_values = [option['subcategory_name'] for option in subcategory_name_option]
    subcategory_name_values_json = json.dumps(subcategory_name_values)

    brand_name_option = db.execute("SELECT distinct brand_name FROM brands")
    brand_name_values = [option['brand_name'] for option in brand_name_option]
    brand_name_values_json = json.dumps(brand_name_values)

    country_of_origin = db.execute("SELECT distinct country_of_origin FROM lssin")
    country_of_origin_values = [option['country_of_origin'] for option in country_of_origin]
    country_of_origin_values_json = json.dumps(country_of_origin_values)


    if product_details:
        product = product_details[0]
        print("gl test:",  gl_description_values_json)  # Add this print statement
        # Pass the JSON string to the template
        return render_template("edit_product.html", product=product, gl_description_values_json=gl_description_values_json, category_name_values_json=category_name_values_json, subcategory_name_values_json=subcategory_name_values_json, brand_name_values_json=brand_name_values_json, country_of_origin_values_json=country_of_origin_values_json)
    else: 
        return "Product not found"


@app.route("/update_product", methods=["POST"])
@login_required
def update_product():
    print("made it to update_product")
    try:
        # Extract JSON data from request
        data = request.get_json()
        LSSIN = data['LSSIN']
        field = data['field']
        value = data['value']
        print("data:", data)

        # Define a dictionary to map field names to SQL statements
        sql_statements = {
            'gl_description': "UPDATE LSSIN SET gl_description = ? WHERE LSSIN = ?", #check
            'category_name': "UPDATE LSSIN SET category_name = ? WHERE LSSIN = ?",#check
            'subcategory_name': "UPDATE LSSIN SET subcategory_name = ? WHERE LSSIN = ?",#check
            'brand_name': "UPDATE LSSIN SET brand_name = ? WHERE LSSIN = ?",#check
            'country_of_origin': "UPDATE LSSIN SET country_of_origin = ? WHERE LSSIN = ?",#check
            'is_vintage': "UPDATE LSSIN SET is_vintage = ? WHERE LSSIN = ?",#check
            'SKU': "UPDATE LSSIN SET SKU = ? WHERE LSSIN = ?",#check
            'variance_type': "UPDATE LSSIN SET variance_type = ? WHERE LSSIN = ?", #check
            'variance': "UPDATE LSSIN SET variance = ? WHERE LSSIN = ?", #check
            'description': "UPDATE LSSIN SET description = ? WHERE LSSIN = ?", #check
            'color_name': "UPDATE LSSIN SET color_name = ? WHERE LSSIN = ?", #check
            'material_type': "UPDATE LSSIN SET material_type = ? WHERE LSSIN = ?", #check
            'msrp': "UPDATE LSSIN SET msrp = ? WHERE LSSIN = ?", #check
            'msrp_tax_amount': "UPDATE LSSIN SET msrp_tax_amount = ? WHERE LSSIN = ?", #check
            'number_of_items': "UPDATE LSSIN SET number_of_items = ? WHERE LSSIN = ?", #check
            'hts_code': "UPDATE LSSIN SET hts_code = ? WHERE LSSIN = ?", #check
            'parent_lssin': "UPDATE LSSIN SET parent_lssin = ? WHERE LSSIN = ?", #check
            'is_base_product': "UPDATE LSSIN SET is_base_product = ? WHERE LSSIN = ?", #check
            'size': "UPDATE LSSIN SET size = ? WHERE LSSIN = ?", #check
            'unit_of_measurement': "UPDATE LSSIN SET unit_of_measurement = ? WHERE LSSIN = ?", #check
            'care_instructions': "UPDATE LSSIN SET care_instructions = ? WHERE LSSIN = ?", #check
            'is_pre_order': "UPDATE LSSIN SET is_pre_order = ? WHERE LSSIN = ?", #check
            'image': "UPDATE LSSIN SET image = ? WHERE LSSIN = ?", #check
        }

        # Get the SQL statement for the given field
        sql = sql_statements.get(field)
        # If the field is not valid, return an error
        if sql is None:
            return jsonify({"success": False, "message": "Invalid field name: " + field}), 400

        # Execute the SQL statement
        print(f"SQL: {sql}, values: ({value}, {LSSIN})")
        db.execute(sql,value, LSSIN)

        if field == 'category_name':
            new_cat_id = db.execute("SELECT category_id FROM categories WHERE category_name = ?", value)
            print("category_id:", new_cat_id)
            db.execute("UPDATE LSSIN SET category_id = ? WHERE LSSIN = ?", new_cat_id[0]['category_id'], LSSIN)
        
        elif field == 'subcategory_name':
            new_subcat_id = db.execute("SELECT subcategory_id FROM subcategories WHERE subcategory_name = ?", value)
            print("subcategory_id:", new_subcat_id)
            db.execute("UPDATE LSSIN SET subcategory_id = ? WHERE LSSIN = ?", new_subcat_id[0]['subcategory_id'], LSSIN)
        
        elif field == 'brand_name':
            new_brand_id = db.execute("SELECT brand_id FROM brands WHERE brand_name = ?", value)
            print("brand_id:", new_brand_id)
            db.execute("UPDATE LSSIN SET brand_id = ? WHERE LSSIN = ?", new_brand_id[0]['brand_id'], LSSIN)

        elif field == 'gl_description':
            new_gl_id = db.execute("SELECT gl FROM gl_product_group WHERE gl_description = ?", value)
            print("gl_id:", new_gl_id)
            db.execute("UPDATE LSSIN SET gl = ? WHERE LSSIN = ?", new_gl_id[0]['gl'], LSSIN)

        # Respond with success message
        return jsonify({"success": True, "message": "Product updated successfully."}), 200
        

    except Exception as e:
        # Respond with error message if something goes wrong
        return jsonify({"success": False, "message": "An error occurred: " + str(e)}), 400
    
@app.route("/add_product/", methods=["GET", "POST"])
@login_required
def add_product():
    
    last_id = db.execute("SELECT MAX(id) FROM lssin")
    new_id = last_id[0]['MAX(id)'] + 1

    gl_description_options = db.execute("SELECT distinct gl_description FROM gl_product_group")
    print(gl_description_options)
    gl_description_values = [option['gl_description'] for option in gl_description_options]
    gl_description_values_json = json.dumps(gl_description_values) # Serialize gl_description_values to a JSON string
    print("gl:", gl_description_values_json)

    category_name_option = db.execute("SELECT distinct category_name FROM categories")
    category_name_values = [option['category_name'] for option in category_name_option]
    category_name_values_json = json.dumps(category_name_values)

    subcategory_name_option = db.execute("SELECT distinct subcategory_name FROM subcategories")
    subcategory_name_values = [option['subcategory_name'] for option in subcategory_name_option]
    subcategory_name_values_json = json.dumps(subcategory_name_values)

    brand_name_option = db.execute("SELECT distinct brand_name FROM brands")
    brand_name_values = [option['brand_name'] for option in brand_name_option]
    brand_name_values_json = json.dumps(brand_name_values)

    country_of_origin = db.execute("SELECT distinct country_of_origin FROM lssin")
    country_of_origin_values = [option['country_of_origin'] for option in country_of_origin]
    country_of_origin_values_json = json.dumps(country_of_origin_values)

    return render_template("add_product.html", new_id=new_id, gl_description_values_json=gl_description_values_json, category_name_values_json=category_name_values_json, subcategory_name_values_json=subcategory_name_values_json, brand_name_values_json=brand_name_values_json, country_of_origin_values_json=country_of_origin_values_json)

@app.route("/add_product_submit", methods=["POST"])
@login_required
def add_product_submit():
    print("made it to add_product_submit")
    try:
        # Extract JSON data from request
        data = request.get_json()
        print("data:", data)

        # Get the last id from the database
        last_id = db.execute("SELECT MAX(id) FROM lssin")
        new_id = str(last_id[0]['MAX(id)'] + 1)
        id = int(last_id[0]['MAX(id)'] + 1)
        prefix = "LS"
        marketplace_id = 1
        
        # Make new LLSIN
        LSSIN = "LS" + new_id

        # Get the LLSIN, gl, category_id, subcategory_id and brand_di from db
        gl_result = db.execute("SELECT gl FROM gl_product_group WHERE gl_description = ?", data.get('gl_description'))
        category_id_result = db.execute("SELECT category_id FROM categories WHERE category_name = ?", data.get('category_name'))
        subcategory_id_result = db.execute("SELECT subcategory_id FROM subcategories WHERE subcategory_name = ?", data.get('subcategory_name'))
        brand_id_result = db.execute("SELECT brand_id FROM brands WHERE brand_name = ?", data.get('brand_name'))
        
        # Get IDs from query results and covert to strings
        gl = int(gl_result[0]['gl']) if gl_result else None
        category_id = int(category_id_result[0]['category_id']) if category_id_result else None
        subcategory_id = str(subcategory_id_result[0]['subcategory_id']) if subcategory_id_result else None
        brand_id = int(brand_id_result[0]['brand_id']) if brand_id_result else None

        # SQL statement for inserting data
        sql_statement = """
        INSERT INTO lssin (
            id, prefix, LSSIN, SKU, marketplace_id, gl, gl_description, 
            item_name, variance_type, variance, image, description, 
            color_name, material_type, msrp, msrp_tax_amount, category_id, 
            category_name, subcategory_id, subcategory_name, brand_id, 
            brand_name, number_of_items, hts_code, parent_lssin, 
            is_base_product, size, unit_of_measurement, country_of_origin, 
            care_instructions, is_vintage, is_pre_order
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """


        # Extract values directly from the data
        values = (
            int(id) if id is not None else None,
            str(prefix) if prefix is not None else None,
            str(LSSIN) if LSSIN is not None else None,
            str(data.get('SKU')) if data.get('SKU') is not None else None,
            int(marketplace_id) if marketplace_id is not None else None,
            int(gl) if gl is not None else None,
            str(data.get('gl_description')) if data.get('gl_description') is not None else None,
            str(data.get('item_name')) if data.get('item_name') is not None else None,
            str(data.get('variance_type')) if data.get('variance_type') is not None else None,
            str(data.get('variance')) if data.get('variance') is not None else None,
            str(data.get('image')) if data.get('image') is not None else None,
            str(data.get('description')) if data.get('description') is not None else None,
            str(data.get('color_name')) if data.get('color_name') is not None else None,
            str(data.get('material_type')) if data.get('material_type') is not None else None,
            int(data.get('msrp')) if data.get('msrp') is not None else None,
            float(data.get('msrp_tax_amount')) if data.get('msrp_tax_amount') is not None else None,
            int(category_id) if category_id is not None else None,
            str(data.get('category_name')) if data.get('category_name') is not None else None,
            int(subcategory_id) if subcategory_id is not None else None,
            str(data.get('subcategory_name')) if data.get('subcategory_name') is not None else None,
            int(brand_id) if brand_id is not None else None,
            str(data.get('brand_name')) if data.get('brand_name') is not None else None,
            int(data.get('number_of_items')) if data.get('number_of_items') is not None else None,
            str(data.get('hts_code')) if data.get('hts_code') is not None else None,
            str(data.get('parent_lssin')) if data.get('parent_lssin') is not None else None,
            str(data.get('is_base_product')) if data.get('is_base_product') is not None else None,
            str(data.get('size')) if data.get('size') is not None else None,
            str(data.get('unit_of_measurement')) if data.get('unit_of_measurement') is not None else None,
            str(data.get('country_of_origin')) if data.get('country_of_origin') is not None else None,
            str(data.get('care_instructions')) if data.get('care_instructions') is not None else None,
            str(data.get('is_vintage')) if data.get('is_vintage') is not None else None,
            str(data.get('is_pre_order')) if data.get('is_pre_order') is not None else None
        )


        # Use the existing database connection
        print("before execute")
        print(values)

        db.execute(sql_statement, *values)
        
        print("after execute")
        
        return jsonify({"success": True, "message": "Product added successfully"}), 200
    except Exception as e:
        # Handle the exception here
        return jsonify({"success": False, "message": "An error occurred: " + str(e)}), 400
