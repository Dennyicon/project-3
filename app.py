# flask_app/app.py
from flask import Flask, request, jsonify
import mysql.connector
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# Load local .env (only for local dev). On Render, set env vars in dashboard.
load_dotenv()

app = Flask(__name__)

# ---------- Cloudinary configuration ----------
cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "denny"),
    api_key    = os.getenv("CLOUDINARY_API_KEY", "329782872631639"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "lz9dpXcu_twdOBANTk9um7faEpM"),
    secure     = True
)

# ---------- MySQL configuration (AwardSpace) ----------
db_config = {
    'user': os.getenv("DB_USER", "4710535_denny"),
    'password': os.getenv("DB_PASSWORD", "uJKacrVf4dL/5w;%"),
    'host': os.getenv("DB_HOST", "fdb1032.awardspace.net"),
    'database': os.getenv("DB_NAME", "4710535_denny"),
    'port': int(os.getenv("DB_PORT", 3306))
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# ---------- Routes ----------

@app.route("/")
def home():
    return jsonify({
        "message": "Flask API is running",
        "routes": {
            "/testdb": "GET - test DB connection",
            "/upload": "POST - upload file (form-data: file)",
            "/files": "GET - list files metadata"
        }
    })

@app.route("/health")
def health():
    return "OK", 200

@app.route("/testdb", methods=["GET"])
def testdb():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"database": row[0]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = file.filename

    # Upload to Cloudinary (direct from FileStorage object)
    try:
        result = cloudinary.uploader.upload(file, resource_type="auto")  # auto handles images/docs/videos
        file_url = result.get("secure_url") or result.get("url")
    except Exception as e:
        return jsonify({"error": f"Cloudinary upload failed: {str(e)}"}), 500

    # Save metadata to MySQL
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (filename, file_path) VALUES (%s, %s)",
            (filename, file_url)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"MySQL error: {str(e)}"}), 500

    return jsonify({"message": "Uploaded", "filename": filename, "url": file_url}), 201

@app.route("/files", methods=["GET"])
def list_files():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM files ORDER BY uploaded_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run locally with python app.py
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)



