from flask import Flask, request, jsonify
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables (.env used only locally)
load_dotenv()

app = Flask(__name__)

# ---------------------------
# Database configuration
# ---------------------------
db_config = {
    'user': os.getenv("DB_USER") or '443133',
    'password': os.getenv("DB_PASSWORD") or 'dennyicon',
    'host': os.getenv("DB_HOST") or 'mysql-denniskingori.alwaysdata.net',
    'database': os.getenv("DB_NAME") or 'denniskingori_denny',
    'port': int(os.getenv("DB_PORT") or 3306)
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# ---------------------------
# HOMEPAGE (Fixes 404 on Render)
# ---------------------------
@app.route("/")
def home():
    return jsonify({
        "message": "API is running successfully",
        "routes": {
            "/testdb": "Test MySQL connection",
            "/upload": "Upload a file (POST)",
            "/files": "List uploaded files"
        }
    })

# ---------------------------
# Render health check
# ---------------------------
@app.route("/health")
def health():
    return "OK", 200

# ---------------------------
# Test DB connection
# ---------------------------
@app.route("/testdb")
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        name = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({"message": f"Connected to: {name[0]}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------
# Upload a file
# ---------------------------
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    os.makedirs("uploads", exist_ok=True)
    save_path = os.path.join("uploads", file.filename)
    file.save(save_path)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO files (filename, file_path) VALUES (%s, %s)",
            (file.filename, save_path)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "File uploaded", "filename": file.filename}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------
# List uploaded files
# ---------------------------
@app.route("/files")
def list_files():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM files ORDER BY uploaded_at DESC")
        files = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(files), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
# Run server
# ---------------------------
if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)


