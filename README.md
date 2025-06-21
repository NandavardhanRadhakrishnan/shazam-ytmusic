# Shazam to YouTube Music API

Upload your Shazam browser extension history (`db.zip`) and automatically import songs into a YouTube Music playlist.

---

## 📦 API Endpoint

**POST** `/upload`

---

## 🔧 Form Data

| Field          | Type   | Description                                               |
| -------------- | ------ | --------------------------------------------------------- |
| `file`         | `file` | The Shazam `.zip` archive (must contain the `db/` folder) |
| `headers_file` | `file` | A JSON file containing your YouTube Music auth headers    |

The `headers_file` should be the exported `headers_auth.json` file from your YouTube Music authenticated session, as used with `ytmusicapi`.

---

## 🧪 Example CURL

```bash
curl --location 'https://shazam-ytmusic.onrender.com/upload' \
--header 'Accept: application/json' \
--form 'file=@"db.zip"' \
--form 'headers_file=@"headers_auth.json"'
```

## Example Response

```json
{
  "status": "success",
  "songs_added": 42,
  "songs_skipped": 15,
  "songs_added_details": ["Track A - Artist A", "Track B - Artist B"],
  "songs_skipped_details": ["Track X - Artist X", "Track Y - Artist Y"],
  "playlist_id": "PLxxxxxxxxxxxxxxxx"
}
```
