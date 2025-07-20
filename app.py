from flask import Flask, render_template, request, send_file
import os
import subprocess
import uuid
import threading
import time

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def aufetch():
    data = request.get_json()
    url = data.get("url")
    format = data.get("format", "audio")

    uid = str(uuid.uuid4())
    file_path = f"{DOWNLOAD_FOLDER}/{uid}"

    try:
        if format == "video":
            output_path = f"{file_path}.%(ext)s"
            subprocess.run([
                "yt-dlp",
                "-f", "bv[height<=720]+ba/b[height<=720]",
                "-o", output_path,
                url
            ], check=True)

            # Find actual filename with extension
            downloaded_files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith(uid)]
            if not downloaded_files:
                return "Video file not found after download", 500

            final_path = os.path.join(DOWNLOAD_FOLDER, downloaded_files[0])
            threading.Thread(target=delayed_delete, args=(final_path, 30), daemon=True).start()
            return send_file(final_path, as_attachment=True)

        else:  # audio
            output_path = f"{file_path}.%(ext)s"
            subprocess.run([
                "yt-dlp",
                "-f", "bestaudio",
                "-o", output_path,
                url
            ], check=True)

            # Find actual filename with extension
            downloaded_files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith(uid)]
            if not downloaded_files:
                return "Audio file not found after download", 500

            final_path = os.path.join(DOWNLOAD_FOLDER, downloaded_files[0])
            threading.Thread(target=delayed_delete, args=(final_path, 30), daemon=True).start()
            return send_file(final_path, as_attachment=True, conditional=True)

    except subprocess.CalledProcessError as e:
        return f"Error downloading: {str(e)}", 500

def delayed_delete(path, delay):
    time.sleep(delay)
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        return e

if __name__ == '__main__':
    app.run(debug=True, threaded=True)