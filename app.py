from flask import Flask, request, jsonify
import mysql.connector
import os
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "yourpassword")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_NAME = os.getenv("DB_NAME", "file_db")
GCS_BUCKET = os.getenv("GCS_BUCKET", "your-gcs-bucket-name")

db_config = {
    'user': DB_USER,
    'password': DB_PASSWORD,
    'host': DB_HOST,
    'database': DB_NAME
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

storage_client = storage.Client()  # uses application default credentials

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message":"No file part"}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({"message":"No selected file"}), 400

    os.makedirs("uploads", exist_ok=True)
    local_path = os.path.join("uploads", f.filename)
    f.save(local_path)

    # upload to GCS
    bucket = storage_client.bucket(GCS_BUCKET)
    blob = bucket.blob(f.filename)
    blob.upload_from_filename(local_path)

    # save metadata in MySQL
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO files (filename, gcs_path) VALUES (%s, %s)",
                (f.filename, f"gs://{GCS_BUCKET}/{f.filename}"))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message":"uploaded", "gcs": f"gs://{GCS_BUCKET}/{f.filename}"}), 201

@app.route("/files", methods=["GET"])
def list_files():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM files ORDER BY uploaded_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
