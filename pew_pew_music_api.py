from flask import Flask, request, jsonify
import psycopg2
import os
from supabase import create_client, Client
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ✅ Supabase Config
SUPABASE_URL = "https://mlylhrqvkbozngbpxrie.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1seWxocnF2a2Jvem5nYnB4cmllIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzE3OTAwMywiZXhwIjoyMDU4NzU1MDAzfQ.RCabVvCurAHHnOGsvLkNAeTjKlUM62IS4Q1bCq0XTto"  # Replace with your actual service role key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ PostgreSQL Database Connection 
DATABASE_URL = "postgresql://postgres:ilymaloni321@db.mlylhrqvkbozngbpxrie.supabase.co:5432/postgres?sslmode=require"

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print("❌ Database connection error:", e)
        return None


@app.route('/getMusic', methods=['GET'])
def get_music():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, title, artist, lyrics, likes, song_url, image_url, created_at FROM songs ORDER BY created_at DESC")
        songs = cursor.fetchall()
        return jsonify([
            {
                "id": s[0], 
                "title": s[1], 
                "artist": s[2], 
                "lyrics": s[3], 
                "likes": s[4], 
                "song_url": s[5], 
                "image_url": s[6], 
                "created_at": str(s[7])  # ✅ Fix: Convert timestamp to string
            }
            for s in songs
        ])
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# ✅ Function to upload file to Supabase Storage (Fixed)
def upload_file(bucket_name, file):
    try:
        filename = secure_filename(file.filename)
        storage_path = f"{filename}"  # ✅ Path fix

        # ✅ File ko bytes me convert karo
        file_data = file.read()

        # ✅ Upload file as bytes
        response = supabase.storage.from_(bucket_name).upload(storage_path, file_data)

        # ✅ Fix: Proper error check
        if isinstance(response, dict) and "error" in response:
            print("❌ Upload Error:", response["error"])
            return None

        # ✅ Fix: Correct public URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{filename}"
        return public_url

    except Exception as e:
        print("❌ Exception in upload:", e)
        return None


# ✅ Function to insert a song in database
def insert_song(title, artist, likes, song_url, image_url, lyrics):
    try:
        response = supabase.table("songs").insert({
            "title": title,
            "artist": artist,
            "likes": likes,
            "song_url": song_url,
            "image_url": image_url,
            "lyrics": lyrics
        }).execute()

        # ✅ Fix: Debugging response
        if response and hasattr(response, "data") and response.data:
            print("✅ Song inserted:", response.data)
            return True
        else:
            print("❌ Failed to insert song")
            return False

    except Exception as e:
        print("❌ Exception in insert_song:", e)
        return False


# ✅ API Route to Add a New Song
@app.route('/addMusic', methods=['POST'])
def add_music():
    title = request.form.get("title")
    artist = request.form.get("artist")
    lyrics = request.form.get("lyrics")
    song_file = request.files.get("song_file")
    image_file = request.files.get("image_file")

    if not all([title, artist, lyrics, song_file, image_file]):
        return jsonify({"error": "Missing required fields"}), 400

    # ✅ Upload song
    song_url = upload_file("music", song_file)
    if not song_url:
        return jsonify({"error": "Failed to upload song"}), 500

    # ✅ Upload image
    image_url = upload_file("images", image_file)
    if not image_url:
        return jsonify({"error": "Failed to upload image"}), 500

    # ✅ Insert song into database
    if insert_song(title, artist, 0, song_url, image_url, lyrics):
        return jsonify({"message": "Song added successfully"}), 201
    else:
        return jsonify({"error": "Failed to insert song into database"}), 500


if __name__ == '__main__':
    app.run()
