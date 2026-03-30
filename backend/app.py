

import os
import re
import uuid
import threading
import subprocess
import time  # Added for time calculations
from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Dictionary to track background jobs
jobs = {}

def cleanup_old_files():
    """Background task that deletes files older than 10 minutes (600 seconds)."""
    while True:
        now = time.time()
        cutoff = now - (5 * 60) # 10 minutes in seconds

        try:
            for filename in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                # Check if it's a file and if its last modification time is older than cutoff
                if os.path.isfile(filepath):
                    file_modified_time = os.path.getmtime(filepath)
                    if file_modified_time < cutoff:
                        print(f"Cleanup: Removing old file {filename}")
                        os.remove(filepath)
                        
                        # Clean up the job entry if it exists
                        job_id = filename.split('_')[0]
                        if job_id in jobs:
                            del jobs[job_id]
        except Exception as e:
            print(f"Cleanup Error: {e}")

        time.sleep(60) # Run the check every minute

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
            jobs[job_id]["status"] = "done"
        else:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = "yt-dlp failed."
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


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

    # The existing @after_this_request already cleans up the specific file 
    # immediately after download. The background thread covers files that 
    # users requested but never actually clicked "Download" on.
    return send_file(filepath, as_attachment=True, download_name=job["filename"])


@app.route("/")
def home():
    return jsonify({"status": "online", "message": "YT Downloader API is running"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
    
    
    
    
    
    
    
# import os
# import re
# import uuid
# import threading
# import subprocess
# from flask import Flask, request, jsonify, send_file, after_this_request
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)

# DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
# os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# jobs = {}


# def parse_progress(line):
#     match = re.search(r"(\d+\.?\d*)%", line)
#     if match:
#         return float(match.group(1))
#     return None


# def build_format_selector(mode, resolution):
#     """Build yt-dlp format string based on mode and resolution."""
#     if mode == "audio":
#         return "bestaudio/best"

#     if resolution == "best":
#         return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

#     h = resolution  # e.g. "1080"
#     return (
#         f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]"
#         f"/bestvideo[height<={h}]+bestaudio"
#         f"/best[height<={h}]"
#         f"/best"
#     )


# def run_download(job_id, url, mode, resolution):
#     jobs[job_id]["status"] = "downloading"
#     output_template = os.path.join(DOWNLOAD_DIR, f"{job_id}_%(title)s.%(ext)s")
#     fmt = build_format_selector(mode, resolution)

#     if mode == "audio":
#         cmd = [
#             "yt-dlp",
#             "--no-playlist",
#             "--format", fmt,
#             "--extract-audio",
#             "--audio-format", "mp3",
#             "--audio-quality", "0",
#             "--newline", "--progress",
#             "--output", output_template,
#             url,
#         ]
#     else:
#         cmd = [
#             "yt-dlp",
#             "--no-playlist",
#             "--format", fmt,
#             "--merge-output-format", "mp4",
#             "--newline", "--progress",
#             "--output", output_template,
#             url,
#         ]

#     try:
#         proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
#         for line in proc.stdout:
#             line = line.strip()
#             pct = parse_progress(line)
#             if pct is not None:
#                 jobs[job_id]["progress"] = min(pct, 99)
#         proc.wait()

#         if proc.returncode == 0:
#             for f in os.listdir(DOWNLOAD_DIR):
#                 if f.startswith(job_id):
#                     jobs[job_id]["filename"] = f
#                     break
#             jobs[job_id]["progress"] = 100
#             jobs[job_id]["status"] = "done"
#         else:
#             jobs[job_id]["status"] = "error"
#             jobs[job_id]["error"] = "yt-dlp failed. Check the URL or try a different resolution."
#     except FileNotFoundError:
#         jobs[job_id]["status"] = "error"
#         jobs[job_id]["error"] = "yt-dlp is not installed. Run: pip install yt-dlp"
#     except Exception as e:
#         jobs[job_id]["status"] = "error"
#         jobs[job_id]["error"] = str(e)


# @app.route("/api/download", methods=["POST"])
# def start_download():
#     data = request.get_json() or {}
#     url = data.get("url", "").strip()
#     mode = data.get("mode", "video")
#     resolution = data.get("resolution", "best")

#     if not url:
#         return jsonify({"error": "URL is required"}), 400

#     job_id = str(uuid.uuid4())
#     jobs[job_id] = {"progress": 0, "status": "queued", "filename": None, "error": None}
#     threading.Thread(target=run_download, args=(job_id, url, mode, resolution), daemon=True).start()
#     return jsonify({"job_id": job_id})


# @app.route("/api/progress/<job_id>")
# def get_progress(job_id):
#     job = jobs.get(job_id)
#     if not job:
#         return jsonify({"error": "Job not found"}), 404
#     return jsonify(job)


# @app.route("/api/file/<job_id>")
# def get_file(job_id):
#     job = jobs.get(job_id)
#     if not job or job["status"] != "done" or not job["filename"]:
#         return jsonify({"error": "File not ready"}), 404
#     filepath = os.path.join(DOWNLOAD_DIR, job["filename"])
#     if not os.path.exists(filepath):
#         return jsonify({"error": "File not found on disk"}), 404

#     @after_this_request
#     def cleanup(response):
#         try:
#             os.remove(filepath)
#             del jobs[job_id]
#         except Exception:
#             pass
#         return response

#     return send_file(filepath, as_attachment=True, download_name=job["filename"])


# if __name__ == "__main__":
#     app.run(debug=True, port=5000)


