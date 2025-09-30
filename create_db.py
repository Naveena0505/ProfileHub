# app.py
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, "static", "uploads")
DB_PATH = os.path.join(APP_ROOT, "people.db")

ALLOWED_EXTENSIONS = {'png','jpg','jpeg'}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.secret_key = "replace-with-a-secure-random-key"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.template_filter('display_dob')
def display_dob(dob_iso):
    # dob_iso is YYYY-MM-DD, return dd-mm-yyyy
    try:
        d = datetime.strptime(dob_iso, "%Y-%m-%d")
        return d.strftime("%d-%m-%Y")
    except:
        return dob_iso

@app.route("/", methods=["GET"])
def index():
    q = request.args.get("q", "").strip()
    results = []
    if q:
        conn = get_db_connection()
        cur = conn.cursor()
        # Search logic:
        # If q is numeric and within ID range, search id exact;
        # Always also search name and phone (LIKE).
        like_q = f"%{q}%"
        params = (q, like_q, like_q)
        # Use CAST for id because q may be text
        # *** CHANGED LIMIT TO 7 PER USER REQUEST ***
        cur.execute("""
            SELECT * FROM people 
            WHERE id = ? 
               OR full_name LIKE ? 
               OR phone LIKE ?
            LIMIT 7
        """, params)
        results = cur.fetchall()
        conn.close()
    return render_template("index.html", results=results, q=q)

@app.route("/profile/<int:person_id>", methods=["GET"])
def profile(person_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Fetch Person Data
    cur.execute("SELECT * FROM people WHERE id = ?", (person_id,))
    person = cur.fetchone()

    if not person:
        conn.close()
        flash("Person not found.", "warning")
        return redirect(url_for('index'))
        
    # 2. Calculate "Total Names" (count of people sharing the same FIRST name)
    # This requires splitting the full_name
    first_name = person['full_name'].split(' ')[0]
    
    # Use LIKE search for simplicity, finding names that start with the same first name.
    cur.execute("SELECT COUNT(id) FROM people WHERE full_name LIKE ?", (f"{first_name} %",))
    name_count = cur.fetchone()[0]
    
    # 3. Calculate Global Gender Ratio (for M:F:O display)
    gender_counts = {}
    
    # Fetch total counts for Male, Female, and Others
    for gender_key, label in [("Male", "M"), ("Female", "F"), ("Other", "O")]:
        cur.execute("SELECT COUNT(id) FROM people WHERE gender = ?", (gender_key,))
        count = cur.fetchone()[0]
        gender_counts[label] = count

    # Format the ratio string (M:5 | F:4 | O:1)
    gender_ratio = f"M:{gender_counts.get('M', 0)} | F:{gender_counts.get('F', 0)}"
    if gender_counts.get("O", 0) > 0:
        gender_ratio += f" | O:{gender_counts['O']}"

    conn.close()
    
    return render_template("profile.html", 
                           person=person, 
                           name_count=name_count, 
                           gender_ratio=gender_ratio)

@app.route("/upload_photo/<int:person_id>", methods=["POST"])
def upload_photo(person_id):
    if 'photo' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('profile', person_id=person_id))
    file = request.files['photo']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('profile', person_id=person_id))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.',1)[1].lower()
        saved_name = f"{person_id}.{ext}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_name)
        # Save file
        file.save(save_path)
        # Resize to passport-ish size (300x300 px) and overwrite
        try:
            img = Image.open(save_path)
            img = img.convert("RGB")
            img.thumbnail((400, 400))  # keep within 400x400
            img.save(save_path, optimize=True, quality=85)
        except Exception as e:
            # if PIL fails, remove file
            if os.path.exists(save_path):
                os.remove(save_path)
            flash("Error processing image.", "danger")
            return redirect(url_for('profile', person_id=person_id))
        # Update DB
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE people SET photo_filename = ? WHERE id = ?", (saved_name, person_id))
        conn.commit()
        conn.close()
        flash("Photo uploaded.", "success")
        return redirect(url_for('profile', person_id=person_id))
    else:
        flash("File type not allowed. Use png/jpg/jpeg.", "danger")
        return redirect(url_for('profile', person_id=person_id))

if __name__ == "__main__":
    # Ensure uploads dir exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host="127.0.0.1", port=5000)
