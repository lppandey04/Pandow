from flask import Flask, render_template, request, send_file
import os
import subprocess
import uuid
import threading
import time

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def aufetch():
    data = request.get_json()
    url = data.get("url")
    format = data.get("format", "audio")

    uid = str(uuid.uuid4())
    output_template = f"{DOWNLOAD_FOLDER}/{uid}.%(ext)s"

    try:
        # Set format and mime type
        if format == "video":
            yt_format = "bv[height<=720]+ba/b[height<=720]"
            mime_type = "video/mp4"
        else:
            yt_format = "bestaudio"
            mime_type = "audio/mpeg"

        # Run yt-dlp
        result = subprocess.run([
            "yt-dlp",
            "--geo-bypass",
            "--force-ipv4",
            "-v",
            "-f", yt_format,
            "-o", output_template,
            url
        ], capture_output=True, text=True)

        if result.returncode != 0:
            return f"Download failed:\n{result.stderr}", 500

        # Retry loop to wait for file to appear
        downloaded_file = None
        for _ in range(10):
            matches = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith(uid)]
            if matches:
                downloaded_file = matches[0]
                break
            time.sleep(0.5)

        if not downloaded_file:
            return "File not found after download", 500

        final_path = os.path.join(DOWNLOAD_FOLDER, downloaded_file)

        if not os.path.exists(final_path):
            return "File seems to be deleted or inaccessible", 500

        # Start auto-delete in background
        threading.Thread(target=delayed_delete, args=(final_path, 30), daemon=True).start()

        return send_file(final_path, as_attachment=True, conditional=True, mimetype=mime_type)

    except Exception as e:
        return f"Unexpected error: {str(e)}", 500

def delayed_delete(path, delay):
    time.sleep(delay)
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error deleting file {path}: {e}")

if __name__ == '__main__':
    app.run(debug=False, threaded=True)
