# Shazam to YouTube Music API

Upload your Shazam browser extension history (`db.zip`) auto-import songs into a YouTube Music playlist.

## 📦 API Endpoint

**POST** `/upload`

### Form Data

- `file`: Shazam `.zip` archive (should contain `db/` folder)

### CURL

```
curl --location 'https://shazam-ytmusic.onrender.com/upload' \
--header 'Accept: application/json' \
--form 'file=@"db.zip"'
```

### Response

```json
{
  "status": "success",
  "songs_added": 42
}
```
