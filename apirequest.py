import eventlet
eventlet.monkey_patch()
from player import play_index_song, play_random, set_time_song, set_volume, get_playlist, rearrange_playlist
from player import previous_song, mains, update_yt_dlp, retrieve_playlist, get_current_song, preload_song
from player import playlist, shuffle_playlist, pause_song, resume_song, next_song, menu_cli, get_time_info
import threading
import signal
import os
import sys
from flask_socketio import SocketIO
from flask import Flask, jsonify, request, render_template



if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")


app = Flask(
    __name__,
    static_folder=os.path.join(base_path, 'static'),
    template_folder=os.path.join(base_path, 'templates')
)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

preload_lock = threading.Lock()  # Lock to prevent multiple executions
preload_thread = None


def emit_time_info():
    while True:
        eventlet.sleep(5)
        current, total = get_time_info()
        socketio.emit("time_update", {"current": current, "total": total})


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/shutdown', methods=['POST'])
def shutdown():
    print("Shutting down...")
    os.kill(os.getpid(), signal.SIGINT)  # Simulate Ctrl+C to kill Flask
    return "Server shutting down..."


def preload_task():
    with preload_lock:  # Ensure only one preload runs at a time
        preload_song()


@app.route('/rearrange_playlist', methods=['POST'])
def order_playlist():
    data = request.json
    rearrange_playlist(data['old'], data['new'])
    return jsonify({"status": "Success"})


@app.route('/playlist', methods=['GET'])
def get_playlists():
    data = get_playlist()
    return jsonify({"playlist": data[0], "current": data[1]})


@app.route('/get_info', methods=['GET'])
def get_info():
    info = get_current_song()
    return jsonify({"title": info[0], "thumbnail": info[1], "index": info[2]})


@app.route('/set_volume', methods=['POST'])
def change_volume():
    data = request.json
    set_volume(data['level'])
    return jsonify({"status": "Volume set"})


@app.route("/set_time", methods=["POST"])
def set_time():
    data = request.get_json()
    seconds = data.get("time")
    if seconds is not None:
        set_time_song(seconds * 1000)  # convertir a milisegundos
        return jsonify({"status": "ok"})
    return jsonify({"error": "missing time"}), 400


@app.route('/play_index_song', methods=['POST'])
def play_index():
    global preload_thread
    # If preload is already running, wait for it to finish
    if preload_thread and preload_thread.is_alive():
        preload_thread.join()  # Wait until the previous preload completes

    # Now that previous preload is finished (or didn't exist), change the track
    data = request.json
    play_index_song(data['index'])

    info = get_current_song()
    socketio.emit('song_changed', {
                  "title": info[0], "thumbnail": info[1]})

    return jsonify({"status": "Playing song"})


@app.route('/shuffle', methods=['POST'])
def shuffle():
    global preload_thread
    if preload_thread and preload_thread.is_alive():
        preload_thread.join()

    shuffle_playlist()
    return jsonify({"status": "Shuffled"})


@app.route('/random_song', methods=['POST'])
def random():
    play_random()
    return jsonify({"status": "Shuffled"})


@app.route('/pause', methods=['POST'])
def pause():
    status = pause_song()
    if status == 0:
        return jsonify({"status": "paused"})
    return jsonify({"error": "No song playing"})


@app.route('/resume', methods=['POST'])
def resume():
    status = resume_song()
    if status == 0:
        return jsonify({"status": "resumed"})
    return jsonify({"error": "Already playing"})


@app.route('/next', methods=['POST'])
def next_track():
    if not playlist:
        return jsonify({"error": "Playlist is empty"}), 500

    data = request.json
    flag = True
    if data['id'] == 0:
        flag = True
    global preload_thread
    # If preload is already running, wait for it to finish
    if preload_thread and preload_thread.is_alive():
        preload_thread.join()  # Wait until the previous preload completes
        if data['id'] == 1:
            flag = False
    # Now that previous preload is finished (or didn't exist), change the track
    if flag:
        next_song()
    # Start a new preload thread
    preload_thread = threading.Thread(target=preload_task)
    preload_thread.start()
    info = get_current_song()

    # Emitir evento al cliente vía WebSocket con la info actualizada
    socketio.emit('song_changed', {
                  "title": info[0], "thumbnail": info[1]})

    return jsonify({"status": "playing next", "title": info[0], "thumbnail": info[1]})


@app.route('/previous', methods=['POST'])
def previous_track():
    if not playlist:
        return jsonify({"error": "Playlist is empty"}), 500
    if preload_thread and preload_thread.is_alive():
        preload_thread.join()

    previous_song()
    info = get_current_song()
    socketio.emit('song_changed', {
                  "title": info[0], "thumbnail": info[1]})
    return jsonify({"status": "playing previous", "title": info[0], "thumbnail": info[1]})


@app.route('/playstart', methods=['POST'])
def start():
    if not playlist:
        return jsonify({"error": "Playlist is empty"}), 500
    mains()
    return jsonify({"status": "playing"})


if __name__ == "__main__":
    # update_yt_dlp()
    retrieve_playlist()
    shuffle_playlist()
    menu_cli()
    socketio.start_background_task(emit_time_info)
    socketio.run(app, host="0.0.0.0", port=5000)
