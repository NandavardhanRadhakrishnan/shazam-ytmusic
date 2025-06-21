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
        if pl['title'].strip().lower() == title.strip().lower():
            print(f"✅ Found existing playlist: {title}")
            return pl['playlistId']
    print(f"📁 Creating new playlist: {title}")
    return ytmusic.create_playlist(title, "Auto-imported from Shazam")


@app.route("/upload", methods=["POST"])
def upload_zip():
    if 'file' not in request.files or 'headers_file' not in request.files:
        return jsonify({"error": "Both .zip file and headers_file are required"}), 400

    file = request.files['file']
    if not file.filename.endswith(".zip"):
        return jsonify({"error": "Only .zip files are accepted"}), 400

    try:
        headers = json.load(request.files['headers_file'])
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
        for item in history["shazam_matches"]:
            title = None
            artist = None
            if item.get("metadata"):
                metadata = item.get("metadata")
                title = metadata.get("title")
                artist = metadata.get("artist", " ")
            elif item.get("attributes"):
                attributes = item.get("attributes")
                title = attributes.get("title")
                artist = attributes.get("primaryArtist")
            if title and artist:
                raw_songs.append(f"{title} - {artist}")
        raw_songs = list(set(raw_songs))

        # Get or create playlist
        playlist_title = "Shazam Playlist"
        playlist_id = get_or_create_playlist(ytmusic, playlist_title)

        # Get existing songs
        existing = ytmusic.get_playlist(playlist_id, limit=2000)
        existing_titles = {
            (track['title'].strip().lower(),
             track['artists'][0]['name'].strip().lower())
            for track in existing['tracks']
        }

        added = 0
        to_add = []
        added_songs = []
        skipped_songs = []
        failed_matches = []

        for song in raw_songs:
            print(f"🔍 Searching: {song}")
            res = ytmusic.search(song, filter="songs")
            if res:
                track = res[0]
                title = track.get('title', '').strip()
                artists = track.get('artists', [])
                artist = artists[0]['name'].strip() if artists else ''
                video_id = track.get("videoId")

                key = (title.lower(), artist.lower())
                if title and artist and video_id:
                    if key not in existing_titles:
                        print(f"✅ Adding: {title} - {artist}")
                        to_add.append(video_id)
                        added_songs.append(f"{title} - {artist}")
                        existing_titles.add(key)
                        added += 1
                    else:
                        skipped_songs.append(f"{title} - {artist}")
                        print(f"⏩ Skipped (duplicate): {title} - {artist}")
                else:
                    failed_matches.append(song)
                    print("⚠️ Incomplete track data, skipped.")
            else:
                failed_matches.append(song)
                print(f"❌ No match found for: {song}")

        if to_add:
            ytmusic.add_playlist_items(playlist_id, to_add)

        return jsonify({
            "status": "success",
            "playlist_id": playlist_id,
            "songs_added": added,
            "total_extracted": len(raw_songs),
            "existing_count": len(existing_titles),
            "added_songs": added_songs,
            "skipped_songs": skipped_songs,
            "failed_matches": failed_matches
        })


@app.route("/", methods=["GET"])
def home():
    return "🎶 Shazam to YouTube Music API is running."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
