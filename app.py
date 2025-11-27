from flask import Flask, request, jsonify
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from .env (local development)
load_dotenv()

app = Flask(__name__)

# ---------------------------
# Database configuration with fallback
# ---------------------------
db_config = {
    'user': os.getenv("DB_USER") or '443133',
    'password': os.getenv("DB_PASSWORD") or 'dennyicon',
    'host': os.getenv("DB_HOST") or 'mysql-denniskingori.alwaysdata.net',
    'database': os.getenv("DB_NAME") or 'denniskingori_denny',
    'port': int(os.getenv("DB_PORT", 3306))
}

# ---------------------------
# Helper function to connect to MySQL
# ---------------------------
def get_db_connection():
    return mysql.connector.connect(**db_config)

# ---------------------------
# Route: Test database connection
# ---------------------------
@app.route("/testdb", methods=['GET'])
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"message": f"Connected to database: {db_name[0]}"}), 200
    except Exception as e:
        return jsonify({"message": f"Database connection error: {str(e)}"}), 500

# ---------------------------
# Route: Upload file
# ---------------------------
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400

    filename = file.filename

    # Create uploads folder if it doesn't exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    file_path = os.path.join('uploads', filename)
    file.save(file_path)

    # Save file info in MySQL
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (filename, file_path) VALUES (%s, %s)",
            (filename, file_path)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": f"File '{filename}' uploaded successfully!"}), 201
    except Exception as e:
        return jsonify({"message": f"MySQL error: {str(e)}"}), 500

# ---------------------------
# Route: List all uploaded files
# ---------------------------
@app.route('/files', methods=['GET'])
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
        return jsonify({"message": f"MySQL error: {str(e)}"}), 500

# ---------------------------
# Main entry point
# ---------------------------
if __name__ == '__main__':
    # Ensure uploads folder exists
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 5000)))

