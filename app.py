# app.py
import os
import sqlite3
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
from fpdf import FPDF

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, "static", "uploads")
DB_PATH = os.path.join(APP_ROOT, "people.db")

ALLOWED_EXTENSIONS = {'png','jpg','jpeg'}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.secret_key = "replace-with-a-secure-random-key"

# --- DATABASE AND HELPER FUNCTIONS ---

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.template_filter('display_dob')
def display_dob(dob_iso):
    try:
        d = datetime.strptime(dob_iso, "%Y-%m-%d")
        return d.strftime("%d-%m-%Y")
    except (ValueError, TypeError):
        return dob_iso

def get_next_id(conn):
    cur = conn.cursor()
    cur.execute("SELECT MAX(id) FROM people")
    max_id = cur.fetchone()[0]
    return 100 if max_id is None or max_id < 100 else max_id + 1

def save_and_resize_photo(file, person_id, upload_folder):
    saved_name = f"{person_id}.jpg"
    save_path = os.path.join(upload_folder, saved_name)
    try:
        img = Image.open(file.stream).convert("RGB")
        img.thumbnail((400, 400))
        img.save(save_path, "JPEG", optimize=True, quality=85)
        return saved_name
    except Exception as e:
        print(f"Error resizing image: {e}")
        if os.path.exists(save_path):
            os.remove(save_path)
        return None

# --- MAIN APPLICATION ROUTES ---

@app.route("/", methods=["GET"])
def index():
    q = request.args.get("q", "").strip()
    results = []
    if q:
        conn = get_db_connection()
        like_q = f"%{q}%"
        results = conn.execute("""
            SELECT * FROM people 
            WHERE CAST(id AS TEXT) = ? OR full_name LIKE ? OR phone LIKE ?
            LIMIT 7
        """, (q, like_q, like_q)).fetchall()
        conn.close()
    return render_template("index.html", results=results, q=q)

@app.route("/profile/<int:person_id>", methods=["GET"])
def profile(person_id):
    conn = get_db_connection()
    person = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
    if not person:
        conn.close()
        flash("Person not found.", "warning")
        return redirect(url_for('index'))

    search_query = request.args.get('search', '').strip()
    if search_query:
        like_query = f"%{search_query}%"
        all_people = conn.execute("""
            SELECT * FROM people WHERE full_name LIKE ? OR phone LIKE ? OR email LIKE ?
            ORDER BY full_name ASC
        """, (like_query, like_query, like_query)).fetchall()
    else:
        all_people = conn.execute("SELECT * FROM people ORDER BY full_name ASC").fetchall()
    conn.close()
    
    return render_template("profile.html", person=person, all_people=all_people, search_query=search_query)

@app.route("/create", methods=["GET", "POST"])
def create_profile():
    conn = get_db_connection()
    if request.method == "POST":
        data = request.form
        file = request.files.get('photo')
        try:
            cur = conn.cursor()
            dob_date = datetime.strptime(data.get('dob'), "%Y-%m-%d")
            age = (datetime.now() - dob_date).days // 365
            new_id = get_next_id(conn)
            
            cur.execute("""
                INSERT INTO people (id, full_name, age, gender, dob, religion, phone, email, address, occupation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_id, data.get('full_name'), age, data.get('gender'), data.get('dob'), data.get('religion'), 
                  data.get('phone'), data.get('email'), data.get('address'), data.get('occupation')))
            conn.commit()
            
            if file and file.filename and allowed_file(file.filename):
                saved_name = save_and_resize_photo(file, new_id, app.config['UPLOAD_FOLDER'])
                if saved_name:
                    cur.execute("UPDATE people SET photo_filename = ? WHERE id = ?", (saved_name, new_id))
                    conn.commit()
            
            conn.close()
            flash(f"✅ New profile for {data.get('full_name')} created with ID {new_id}.", "success")
            return redirect(url_for('profile', person_id=new_id))
        except sqlite3.IntegrityError:
            conn.close()
            flash("Error: Phone number or Email already exists.", "danger")
        except Exception as e:
            conn.close()
            flash(f"An error occurred: {e}", "danger")
        return redirect(url_for('create_profile'))

    next_id = get_next_id(conn)
    conn.close()
    return render_template("create_profile.html", next_id=next_id)

@app.route("/update_profile/<int:person_id>", methods=["POST"])
def update_profile(person_id):
    data = request.form
    file = request.files.get('photo')
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        dob_date = datetime.strptime(data.get('dob'), "%Y-%m-%d")
        age = (datetime.now() - dob_date).days // 365
        
        cur.execute("""
            UPDATE people SET
                full_name = ?, age = ?, gender = ?, dob = ?, religion = ?,
                phone = ?, email = ?, address = ?, occupation = ?
            WHERE id = ?
        """, (data.get('full_name'), age, data.get('gender'), data.get('dob'), data.get('religion'), 
              data.get('phone'), data.get('email'), data.get('address'), data.get('occupation'), person_id))
        
        if file and file.filename and allowed_file(file.filename):
            saved_name = save_and_resize_photo(file, person_id, app.config['UPLOAD_FOLDER'])
            if saved_name:
                cur.execute("UPDATE people SET photo_filename = ? WHERE id = ?", (saved_name, person_id))
        
        conn.commit()
        conn.close()
        flash(f"✅ Profile for ID {person_id} updated successfully!", "success")
    except sqlite3.IntegrityError:
        flash("Error: Phone number or Email already exists. Changes not saved.", "danger")
    except Exception as e:
        flash(f"An error occurred: {e}", "danger")
    return redirect(url_for('profile', person_id=person_id))

@app.route("/delete_profile/<int:person_id>")
def delete_profile(person_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM people WHERE id = ?", (person_id,))
    conn.commit()
    conn.close()
    flash(f"Profile ID {person_id} has been deleted.", "info")
    return redirect(request.referrer or url_for('index'))

# --- DATA EXPORT ROUTES ---

@app.route("/export_csv")
def export_csv():
    conn = get_db_connection()
    search_query = request.args.get('search', '').strip()
    if search_query:
        like_query = f"%{search_query}%"
        people_data = conn.execute("""
            SELECT * FROM people WHERE full_name LIKE ? OR phone LIKE ? ORDER BY full_name
        """, (like_query, like_query)).fetchall()
    else:
        people_data = conn.execute("SELECT * FROM people ORDER BY full_name").fetchall()
    conn.close()

    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], "export_data.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Date of Birth", "Gender", "Phone", "Email", "Address", "Occupation", "Religion"])
        for person in people_data:
            writer.writerow([person['id'], person['full_name'], display_dob(person['dob']), person['gender'], 
                             person['phone'], person['email'], person['address'], person['occupation'], person['religion']])
    
    return send_file(csv_path, as_attachment=True)

@app.route("/export_pdf")
def export_pdf():
    conn = get_db_connection()
    search_query = request.args.get('search', '').strip()
    if search_query:
        like_query = f"%{search_query}%"
        people_data = conn.execute("""
            SELECT * FROM people WHERE full_name LIKE ? OR phone LIKE ? ORDER BY full_name
        """, (like_query, like_query)).fetchall()
    else:
        people_data = conn.execute("SELECT * FROM people ORDER BY full_name").fetchall()
    conn.close()

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Personal Information Data", 0, 1, 'C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 8)
    
    # CORRECTED: Changed 'full_name' key to 'name' to match header logic
    col_widths = {'name': 40, 'dob': 20, 'gender': 15, 'phone': 25, 'email': 45, 'address': 60, 'occupation': 30}
    headers = ["Name", "DOB", "Gender", "Phone", "Email", "Address", "Occupation"]
    
    for header in headers:
        key = header.lower().replace(" ", "_")
        pdf.cell(col_widths[key], 10, header, 1, 0, 'C')
    pdf.ln()

    pdf.set_font("Arial", '', 8)
    for person in people_data:
        # CORRECTED: Use 'full_name' to get data, but 'name' for width
        pdf.cell(col_widths['name'], 10, person['full_name'], 1, 0)
        pdf.cell(col_widths['dob'], 10, display_dob(person['dob']), 1, 0)
        pdf.cell(col_widths['gender'], 10, person['gender'], 1, 0)
        pdf.cell(col_widths['phone'], 10, person['phone'], 1, 0)
        pdf.cell(col_widths['email'], 10, person['email'], 1, 0)
        pdf.cell(col_widths['address'], 10, person['address'], 1, 0)
        pdf.cell(col_widths['occupation'], 10, person['occupation'], 1, 0)
        pdf.ln()
    
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], "export_data.pdf")
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True)


# --- SCRIPT EXECUTION ---

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host="127.0.0.1", port=5000)
