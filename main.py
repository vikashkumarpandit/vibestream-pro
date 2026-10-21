import os
import threading
import requests
from flask import Flask, render_template_string, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "downloads")
VAULT_FOLDER = os.path.join(BASE_DIR, "vault_storage")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(VAULT_FOLDER, exist_ok=True)

# Helper: Direct Fast Audio Source
def get_direct_audio(query):
    clean = query.replace('official audio', '').replace('audio', '').strip()
    urls = [
        f"https://saavn.dev/api/search/songs?query={requests.utils.quote(clean)}&limit=1",
        f"https://jiosaavn-api-privatecvc2.vercel.app/search/songs?query={requests.utils.quote(clean)}&limit=1"
    ]
    for u in urls:
        try:
            r = requests.get(u, timeout=5).json()
            res = r.get('data', {}).get('results', []) or r.get('data', [])
            if res:
                dl = res[0].get('downloadUrl', [])
                if dl:
                    return dl[-1].get('url') or dl[-1].get('link')
        except Exception:
            continue
    return None

# HTML UI Template (All-in-One)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>VibeStream Standalone</title>
    <style>
        :root { --bg: #090d16; --card: rgba(30, 41, 59, 0.75); --accent: #10b981; --text: #f8fafc; --subtext: #94a3b8; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
        body { background: var(--bg); color: var(--text); padding-bottom: 120px; overflow-x: hidden; }
        header { position: sticky; top: 0; z-index: 20; background: rgba(9, 13, 22, 0.95); padding: 14px 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.06); }
        .logo { font-size: 1.25rem; font-weight: 800; color: var(--accent); }
        .container { padding: 15px; }
        .search-bar { display: flex; gap: 8px; margin-bottom: 16px; }
        .search-bar input { flex: 1; padding: 12px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); background: #0f172a; color: #fff; outline: none; }
        .search-bar button { padding: 0 18px; border-radius: 12px; border: none; background: var(--accent); color: #052e16; font-weight: 700; }
        .song-list { display: flex; flex-direction: column; gap: 10px; }
        .song-card { display: flex; align-items: center; gap: 12px; background: var(--card); padding: 10px; border-radius: 12px; cursor: pointer; }
        .song-card img { width: 50px; height: 50px; border-radius: 8px; object-fit: cover; }
        .song-info { flex: 1; overflow: hidden; }
        .song-title { font-size: 0.95rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .song-artist { font-size: 0.78rem; color: var(--subtext); margin-top: 3px; }
        .player-bar { position: fixed; bottom: 0; left: 0; right: 0; background: #0f172a; padding: 12px; display: flex; align-items: center; gap: 12px; border-top: 1px solid rgba(255,255,255,0.1); z-index: 50; }
        .player-bar audio { flex: 1; height: 35px; }
    </style>
</head>
<body>
    <header>
        <div class="logo">⚡ VibeStream Pro</div>
    </header>
    <div class="container">
        <div class="search-bar">
            <input type="text" id="searchInput" placeholder="Search song or artist..." onkeypress="if(event.key==='Enter') searchMusic()">
            <button onclick="searchMusic()">Search</button>
        </div>
        <div class="song-list" id="songList"></div>
    </div>
    <div class="player-bar">
        <audio id="audioPlayer" controls></audio>
    </div>
<script>
    async function loadTrending() {
        const res = await fetch('/api/trending');
        const data = await res.json();
        renderSongs(data.songs || []);
    }
    async function searchMusic() {
        const q = document.getElementById('searchInput').value;
        if(!q) return;
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        renderSongs(data.songs || []);
    }
    function renderSongs(songs) {
        const list = document.getElementById('songList');
        list.innerHTML = '';
        songs.forEach(s => {
            const div = document.createElement('div');
            div.className = 'song-card';
            div.innerHTML = `
                <img src="${s.thumbnail}">
                <div class="song-info">
                    <div class="song-title">${s.title}</div>
                    <div class="song-artist">${s.artist}</div>
                </div>
            `;
            div.onclick = () => playSong(s.query);
            list.appendChild(div);
        });
    }
    async function playSong(q) {
        const res = await fetch(`/api/stream?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        if(data.stream_url) {
            const player = document.getElementById('audioPlayer');
            player.src = data.stream_url;
            player.play();
        }
    }
    window.onload = loadTrending;
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/trending')
def trending():
    try:
        res = requests.get("https://itunes.apple.com/in/rss/topsongs/limit=50/json", timeout=5).json()
        songs = []
        for item in res.get('feed', {}).get('entry', []):
            t = item['im:name']['label']
            a = item['im:artist']['label']
            th = item['im:image'][-1]['label']
            songs.append({'title': t, 'artist': a, 'thumbnail': th, 'query': f"{t} {a}"})
        return jsonify({'songs': songs})
    except Exception:
        return jsonify({'songs': []})

@app.route('/api/search')
def search():
    q = request.args.get('q', '')
    try:
        url = f"https://itunes.apple.com/search?term={requests.utils.quote(q)}&country=IN&media=music&limit=40"
        res = requests.get(url, timeout=5).json()
        songs = []
        for item in res.get('results', []):
            t = item.get('trackName', '')
            a = item.get('artistName', '')
            th = item.get('artworkUrl100', '')
            songs.append({'title': t, 'artist': a, 'thumbnail': th, 'query': f"{t} {a}"})
        return jsonify({'songs': songs})
    except Exception:
        return jsonify({'songs': []})

@app.route('/api/stream')
def stream():
    q = request.args.get('q', '')
    direct = get_direct_audio(q)
    if direct:
        return jsonify({'stream_url': direct})
    
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{q}", download=False)
            if 'entries' in info: info = info['entries'][0]
            return jsonify({'stream_url': info.get('url')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
