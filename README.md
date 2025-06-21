# Shazam to YouTube Music API

Upload your Shazam browser extension history (`db.zip`) + your own `ytmusicapi` auth headers to auto-import songs into a YouTube Music playlist.

## 📦 API Endpoint

**POST** `/upload`

### Form Data

- `file`: Shazam `.zip` archive (should contain `db/` folder)
- `headers_auth_json`: Raw JSON content of your YouTube Music auth headers

### Response

```json
{
  "status": "success",
  "songs_added": 42
}
```
