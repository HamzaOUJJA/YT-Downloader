# YTDL Extractor

A self-hosted YouTube downloader with a React frontend and Flask backend. No authentication required.

## Requirements

- Python 3.9+
- Node.js 18+
- [ffmpeg](https://ffmpeg.org/download.html) installed and in your PATH
- yt-dlp (installed via pip below)

---

## Backend Setup

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The backend runs at **http://localhost:5000**

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at **http://localhost:3000**

---

## How It Works

1. Paste any YouTube URL into the input field
2. Choose **VIDEO (MP4)** or **AUDIO (MP3)**
3. Click **INITIATE DOWNLOAD** — a job is created on the server
4. The animated progress bar polls the server every 600ms
5. When complete, click **SAVE FILE** to download it to your device

### Architecture

```
Browser (React)
  │
  ├── POST /api/download  →  Flask spawns yt-dlp subprocess (threaded)
  ├── GET  /api/progress/:id  →  polls until done/error
  └── GET  /api/file/:id  →  streams the file, then auto-deletes it
```

### File handling
- Downloaded files are stored temporarily in `backend/downloads/`
- Files are automatically deleted from the server after being sent to the browser

---

## Notes

- For audio, yt-dlp uses ffmpeg internally to convert to MP3
- The `--no-playlist` flag ensures only single videos are downloaded
- For best quality video, yt-dlp downloads video+audio streams separately and merges them with ffmpeg
