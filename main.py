from flask import Flask, request, jsonify
import os
import zipfile
import json
import tempfile
import plyvel
from ytmusicapi import YTMusic

app = Flask(__name__)


def get_or_create_playlist(ytmusic, title):
    playlists = ytmusic.get_library_playlists()
    for pl in playlists:
        if pl['title'].lower() == title.lower():
            return pl['playlistId']
    return ytmusic.create_playlist(title, "Auto-imported from Shazam")


@app.route("/upload", methods=["POST"])
def upload_zip():
    if 'file' not in request.files or 'headers_auth_json' not in request.form:
        return jsonify({"error": "Both .zip file and headers_auth_json are required"}), 400

    file = request.files['file']
    if not file.filename.endswith(".zip"):
        return jsonify({"error": "Only .zip files are accepted"}), 400

    try:
        headers = json.loads(request.form['headers_auth_json'])
        ytmusic = YTMusic(headers)
    except Exception as e:
        return jsonify({"error": f"Invalid auth headers: {str(e)}"}), 400

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "db.zip")
        file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        db_path = os.path.join(temp_dir, "db")
        if not os.path.exists(db_path):
            return jsonify({"error": "Missing 'db' folder in ZIP"}), 400

        try:
            db = plyvel.DB(db_path, create_if_missing=False)
            history = {}
            for key, value in db:
                try:
                    history[key.decode()] = json.loads(value.decode())
                except:
                    history[key.decode()] = value.decode(errors="ignore")
            db.close()
        except Exception as e:
            return jsonify({"error": f"LevelDB read failed: {str(e)}"}), 500

        # Extract songs
        raw_songs = []
        for item in history.values():
            if isinstance(item, dict) and "track" in item:
                track = item["track"]
                title = track.get("title")
                artist = track.get("subtitle")
                if title and artist:
                    raw_songs.append(f"{title} - {artist}")
        raw_songs = list(set(raw_songs))  # dedupe

        # Get or create playlist
        playlist_title = "Shazam Playlist"
        playlist_id = get_or_create_playlist(ytmusic, playlist_title)

        # Get existing songs to avoid duplicates
        existing = ytmusic.get_playlist(playlist_id, limit=1000)
        existing_titles = {
            (track['title'].strip(), track['artists'][0]['name'].strip())
            for track in existing['tracks']
        }

        # Search and add new songs
        added = 0
        to_add = []
        for song in raw_songs:
            res = ytmusic.search(song, filter="songs")
            if res:
                track = res[0]
                title = track.get('title', '').strip()
                artists = track.get('artists', [])
                artist = artists[0]['name'].strip() if artists else ''
                video_id = track.get("videoId")

                if title and artist and video_id:
                    if (title, artist) not in existing_titles:
                        to_add.append(video_id)
                        # Avoid local dupes
                        existing_titles.add((title, artist))
                        added += 1

        if to_add:
            ytmusic.add_playlist_items(playlist_id, to_add)

        return jsonify({"status": "success", "songs_added": added, "playlist_id": playlist_id})


@app.route("/", methods=["GET"])
def home():
    return "🎶 Shazam to YouTube Music API is running."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
