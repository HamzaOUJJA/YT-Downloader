# 🎬 YT-Downloader — Free YouTube Video Downloader

> A full-stack web application that lets you download YouTube videos and extract audio directly from your browser. Supports MP4 video (up to 4K) and MP3 audio formats.

🌐 **Live Demo:** [https://yt-down-hamza-oujja.vercel.app/](https://yt-down-hamza-oujja.vercel.app/)


![YT-Downloader UI](./preview.png)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Environment Variables](#environment-variables)
- [How It Works](#how-it-works)
- [Deployment](#deployment)
- [Developer](#developer)

---

## Overview

YT-Downloader is a full-stack web application with a **React** frontend and a **Flask** backend. The user pastes a YouTube URL, selects a format and resolution, and the backend handles the download asynchronously using `yt-dlp`. The frontend polls the server for progress updates and presents a real-time download status with a progress bar and wave animation. Once complete, the file is served directly to the user's browser.

---

## Features

- ⚡ **Fast Downloads** — leverages `yt-dlp` for maximum download speed
- 🎥 **Video (MP4)** — supports resolutions from 360p up to 4K (2160p)
- 🎵 **Audio (MP3)** — extracts audio at the highest available quality
- 📊 **Real-time Progress** — live progress bar updated via polling (every 600ms)
- 🌊 **Wave Animation** — visual feedback while a download is in progress
- 🔄 **Background Job System** — each download runs in a dedicated thread
- 🧹 **Auto Cleanup** — downloaded files are automatically deleted after 5 minutes
- 📱 **Responsive Design** — works on desktop, tablet, and mobile browsers
- 🌐 **Multi-platform Support** — compatible with YouTube, Instagram, TikTok, Twitter, Facebook, and more (via yt-dlp)

---

## Tech Stack

### Frontend

| Technology | Role |
|---|---|
| **React 18** | UI framework |
| **Vite** | Build tool and dev server |
| **CSS (custom)** | Styling — no UI library dependency |
| **Fetch API** | HTTP requests to the backend |

### Backend

| Technology | Role |
|---|---|
| **Python 3** | Runtime |
| **Flask** | Web framework / REST API |
| **Flask-CORS** | Cross-Origin Resource Sharing |
| **yt-dlp** | Video/audio downloading engine |
| **threading** | Concurrent download jobs |
| **subprocess** | Running yt-dlp as a child process |
| **uuid** | Unique job ID generation |

### Deployment

| Technology | Role |
|---|---|
| **Vercel** | Frontend hosting (`vercel.json`) |
| **Vercel** | Backend hosting (`vercel.json` in `/backend`) |

---

## Project Structure

```
yt-downloader/
├── backend/
│   ├── downloads/             # Temporary downloaded files (auto-cleaned)
│   ├── venv/                  # Python virtual environment
│   ├── app.py                 # Flask application — main entry point
│   ├── requirements.txt       # Python dependencies
│   └── vercel.json            # Vercel deployment config for backend
│
├── frontend/
│   ├── node_modules/
│   ├── public/
│   │   └── favicon.svg
│   ├── src/
│   │   ├── App.jsx            # Main React component
│   │   ├── App.css            # Application styles
│   │   ├── index.css          # Global styles
│   │   └── main.jsx           # React entry point
│   ├── .env                   # Local environment variables (gitignored)
│   ├── .env.example           # Example env file
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── vercel.json            # Vercel deployment config for frontend
│
├── .gitignore
└── README.md
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     Browser                         │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │           React Frontend (Vite)             │   │
│  │                                             │   │
│  │  1. User pastes URL + selects options       │   │
│  │  2. POST /api/download  ──────────────────► │   │
│  │  3. Poll GET /api/progress/:id  (600ms)     │   │
│  │  4. GET /api/file/:id  (on completion)      │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (JSON)
┌──────────────────────▼──────────────────────────────┐
│              Flask Backend (Python)                 │
│                                                     │
│  POST /api/download                                 │
│    └─► Creates job (uuid) → spawns Thread           │
│                                                     │
│  Thread:                                            │
│    └─► Runs yt-dlp subprocess                       │
│    └─► Parses stdout for % progress                 │
│    └─► Updates jobs{} dict in memory                │
│                                                     │
│  GET /api/progress/:id                              │
│    └─► Returns job status + progress %              │
│                                                     │
│  GET /api/file/:id                                  │
│    └─► Serves file as attachment                    │
│                                                     │
│  Background cleanup thread                          │
│    └─► Removes files older than 5 min (every 60s)   │
└─────────────────────────────────────────────────────┘
```

---

## API Reference

### `POST /api/download`

Starts a new download job.

**Request Body (JSON)**

```json
{
  "url": "https://www.youtube.com/watch?v=xxxx",
  "mode": "video",        // "video" | "audio"
  "resolution": "best"    // "best" | "2160" | "1440" | "1080" | "720" | "480" | "360"
}
```

**Response**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### `GET /api/progress/:job_id`

Returns the current state of a download job.

**Response**

```json
{
  "status": "downloading",   // "queued" | "downloading" | "done" | "error"
  "progress": 77.4,          // 0 – 100
  "filename": null,          // populated when done
  "error": null              // populated on error
}
```

---

### `GET /api/file/:job_id`

Downloads the completed file. Only available when `status === "done"`.

**Response:** Binary file stream with `Content-Disposition: attachment`.

---

### `GET /`

Health check endpoint.

**Response**

```json
{
  "status": "online",
  "message": "YT Downloader API is running"
}
```

---

## Getting Started

### Prerequisites

- **Node.js** >= 18
- **Python** >= 3.9
- **pip**
- **yt-dlp** (`pip install yt-dlp`)
- **ffmpeg** (required by yt-dlp for merging video/audio streams)

Install ffmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows
winget install ffmpeg
```

---

### Backend Setup

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Flask server
python app.py
```

The backend starts on `http://localhost:5000`.

---

### Frontend Setup

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Configure the environment
cp .env.example .env
# Edit .env and set VITE_API_URL=http://localhost:5000/api

# 4. Start the development server
npm run dev
```

The frontend starts on `http://localhost:5173`.

---

## Environment Variables

### Frontend — `frontend/.env`

```env
VITE_API_URL=http://localhost:5000/api
```

For production, replace with your deployed backend URL:

```env
VITE_API_URL=https://your-backend.vercel.app/api
```

---

## How It Works

1. **User submits a URL** — The React frontend sends a `POST` request to `/api/download` with the URL, output mode (video/audio), and desired resolution.

2. **Job creation** — The Flask backend generates a unique `job_id` (UUID), registers the job in an in-memory dictionary, and spawns a background thread.

3. **yt-dlp execution** — The thread runs `yt-dlp` as a subprocess with the appropriate format selector. `stdout` is parsed line by line to extract the download percentage using a regex (`\d+\.?\d*%`).

4. **Progress polling** — The frontend polls `GET /api/progress/:id` every 600 ms and updates the progress bar and wave animation in real time.

5. **File delivery** — Once `status === "done"`, the frontend enables the "Save File" button. Clicking it triggers `GET /api/file/:id`, which streams the file to the browser as an attachment.

6. **Cleanup** — A daemon thread runs every 60 seconds and deletes any file in the `downloads/` folder that was created more than 5 minutes ago, keeping disk usage low.

### Format Selection Logic

| Mode | Resolution | yt-dlp Format String |
|------|------------|----------------------|
| Audio | — | `bestaudio/best` → extracted as MP3 |
| Video | best | `bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best` |
| Video | specific (e.g. 1080) | `bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/...` with fallbacks |

---

## Deployment

Both the frontend and backend include a `vercel.json` configuration for deployment on **Vercel**.

```bash
# Deploy backend
cd backend
vercel --prod

# Deploy frontend (set VITE_API_URL to your backend URL first)
cd frontend
vercel --prod
```

> **Note:** Vercel serverless functions have a maximum execution timeout. For very long videos, consider a dedicated server (e.g. Railway, Render, or a VPS) to avoid timeouts.

---

## Developer

**Hamza OUJJA** — Engineer specialized in Data & AI, based in France.

[![Email](https://img.shields.io/badge/Email-hamzaoujja08%40gmail.com-blue?style=flat-square&logo=gmail)](mailto:hamzaoujja08@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-HamzaOUJJA-black?style=flat-square&logo=github)](https://github.com/HamzaOUJJA)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-hamza--oujja-blue?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/hamza-oujja)

---

© 2024 YT-Download — Premium Video & Audio Extraction. Completely Free Access.
