import os
import re
import uuid
import threading
import subprocess
import time
import pickle
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    build = None
    MediaFileUpload = None
    Credentials = None
    InstalledAppFlow = None
    Request = None

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "token.pickle")
CLIENT_SECRET_PATH = os.path.join(os.path.dirname(__file__), "client_secret.json")

# Dictionary to track background jobs
jobs = {}

drive_service = None


def get_drive_service():
    global drive_service
    if drive_service is not None:
        return drive_service

    if build is None or InstalledAppFlow is None:
        print("[DEBUG] Google API libraries not installed")
        return None

    if not os.path.exists(CLIENT_SECRET_PATH):
        print(f"[DEBUG] client_secret.json not found at {CLIENT_SECRET_PATH}")
        return None

    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[DEBUG] Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("[DEBUG] Opening browser for Google login...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)
        print("[DEBUG] Token saved successfully")

    drive_service = build("drive", "v3", credentials=creds)
    print("[DEBUG] Drive service initialized successfully")
    return drive_service


def upload_to_drive(filepath, filename):
    service = get_drive_service()
    if service is None:
        print("[DEBUG] Drive service is None - check client_secret.json")
        return None, None, "Drive service unavailable"

    file_metadata = {"name": filename}
    folder_id = os.environ.get("GDRIVE_FOLDER_ID")
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(filepath, resumable=True)
    try:
        print(f"[DEBUG] Uploading {filename} to Drive...")
        created_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,webViewLink",
        ).execute()
        print(f"[DEBUG] Upload successful: {created_file.get('webViewLink')}")
        return created_file.get("id"), created_file.get("webViewLink"), None
    except Exception as e:
        print(f"[DEBUG] Drive upload error: {e}")
        return None, None, str(e)


def schedule_file_deletion(job_id, filepath, delay=600):
    def delete_later():
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            jobs.pop(job_id, None)
        except Exception as e:
            print(f"Scheduled deletion failed for {filepath}: {e}")

    threading.Timer(delay, delete_later).start()


def cleanup_old_files():
    """Background task that deletes files older than 10 minutes (600 seconds)."""
    while True:
        now = time.time()
        cutoff = now - (10 * 60)

        try:
            for filename in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.isfile(filepath):
                    file_modified_time = os.path.getmtime(filepath)
                    if file_modified_time < cutoff:
                        print(f"Cleanup: Removing old file {filename}")
                        os.remove(filepath)
                        job_id = filename.split('_')[0]
                        if job_id in jobs:
                            del jobs[job_id]
        except Exception as e:
            print(f"Cleanup Error: {e}")

        time.sleep(60)


# Start the cleanup thread as a daemon (closes when app closes)
threading.Thread(target=cleanup_old_files, daemon=True).start()


def parse_progress(line):
    match = re.search(r"(\d+\.?\d*)%", line)
    if match:
        return float(match.group(1))
    return None


def build_format_selector(mode, resolution):
    """Build yt-dlp format string based on mode and resolution."""
    if mode == "audio":
        return "bestaudio/best"
    if resolution == "best":
        return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    h = resolution
    return (
        f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]"
        f"/bestvideo[height<={h}]+bestaudio"
        f"/best[height<={h}]"
        f"/best"
    )


def run_download(job_id, url, mode, resolution):
    jobs[job_id]["status"] = "downloading"
    output_template = os.path.join(DOWNLOAD_DIR, f"{job_id}_%(title)s.%(ext)s")
    fmt = build_format_selector(mode, resolution)

    print(f"[DEBUG] Starting download: {url}, mode={mode}, resolution={resolution}")

    if mode == "audio":
        cmd = [
            "yt-dlp", "--no-playlist", "--format", fmt,
            "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0",
            "--newline", "--progress", "--output", output_template, url,
        ]
    else:
        cmd = [
            "yt-dlp", "--no-playlist", "--format", fmt,
            "--merge-output-format", "mp4", "--newline", "--progress",
            "--output", output_template, url,
        ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in proc.stdout:
            line = line.strip()
            pct = parse_progress(line)
            if pct is not None:
                jobs[job_id]["progress"] = min(pct, 99)
        proc.wait()

        if proc.returncode == 0:
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(job_id):
                    jobs[job_id]["filename"] = f
                    break
            jobs[job_id]["progress"] = 100

            filepath = os.path.join(DOWNLOAD_DIR, jobs[job_id]["filename"])
            jobs[job_id]["status"] = "uploading"

            drive_id, drive_url, drive_error = upload_to_drive(filepath, jobs[job_id]["filename"])

            if drive_error:
                jobs[job_id]["status"] = "error"
                jobs[job_id]["error"] = f"Google Drive upload failed: {drive_error}"
                return

            if drive_id:
                jobs[job_id]["drive_id"] = drive_id
                jobs[job_id]["drive_url"] = drive_url
                jobs[job_id]["status"] = "done"
                jobs[job_id]["uploaded_at"] = time.time()
            else:
                jobs[job_id]["status"] = "done"

            schedule_file_deletion(job_id, filepath)
        else:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = "yt-dlp failed."
            print(f"[DEBUG] yt-dlp failed for job {job_id}")
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        print(f"[DEBUG] Exception: {e}")


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    mode = data.get("mode", "video")
    resolution = data.get("resolution", "best")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"progress": 0, "status": "queued", "filename": None, "error": None}
    threading.Thread(target=run_download, args=(job_id, url, mode, resolution), daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/api/progress/<job_id>")
def get_progress(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/file/<job_id>")
def get_file(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "done" or not job["filename"]:
        return jsonify({"error": "File not ready"}), 404
    filepath = os.path.join(DOWNLOAD_DIR, job["filename"])
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found on disk"}), 404

    return send_file(filepath, as_attachment=True, download_name=job["filename"])


@app.route("/")
def home():
    return jsonify({"status": "online", "message": "YT Downloader API is running"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)