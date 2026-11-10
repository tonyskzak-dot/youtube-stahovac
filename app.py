import os
import uuid
from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    mode = data.get('mode') # 'audio' nebo 'video'
    quality = data.get('quality')

    if not url:
        return jsonify({'error': 'Zadej platnou URL adresu!'}), 400

    file_id = str(uuid.uuid4())
    out_template = os.path.join(DOWNLOAD_FOLDER, f'{file_id}_%(title)s.%(ext)s')

    ydl_opts = {
        'outtmpl': out_template,
        'quiet': True,
    }

    if mode == 'audio':
        bitrate = quality if quality in ['320', '256', '128'] else '192'
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': bitrate,
            }],
        })
    else:
        if quality == '1080':
            ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality == '720':
            ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if mode == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'

        downloaded_files = [os.path.join(DOWNLOAD_FOLDER, f) for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith(file_id)]
        if not downloaded_files:
            return jsonify({'error': 'Soubor se nepodařilo najít po stažení.'}), 500
        
        target_file = downloaded_files[0]
        actual_filename = os.path.basename(target_file).replace(f'{file_id}_', '')

        response = send_file(target_file, as_attachment=True, download_name=actual_filename)
        
        @response.call_on_closing
        def cleanup():
            try:
                if os.path.exists(target_file):
                    os.remove(target_file)
            except Exception:
                pass

        return response
    
    catch Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)