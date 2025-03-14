import subprocess
import json
import requests
from time import sleep
from pathlib import Path
from random import shuffle, randint
import vlc

player = None
instance = None
playlist = []
Current = 0
paused = False


def get_playlist():
    global playlist, Current
    return playlist, Current


def rearrange_playlist(old_pos, new_pos):
    global playlist
    playlist.pop(new_pos, playlist.pop(old_pos))


def eliminar_archivos():
    carpeta_path = Path(__file__).parent.resolve()
    for archivo in carpeta_path.glob("*.webm"):
        try:
            archivo.unlink()
        except Exception as e:
            return -1


def update_yt_dlp() -> int:
    try:
        result = subprocess.run(["python", "-m", "pip", "install",
                                "--upgrade", "yt-dlp"], capture_output=True, text=True)

        if result.returncode == 0:
            return 0
        else:
            return -1
    except Exception as e:
        return -2


def retrieve_playlist():
    global playlist
    ydl_opts = [
        "python", "-m", "yt_dlp",
        "--flat-playlist",  # No descarga info extra, solo lo básico
        "--print-json",
        "https://youtube.com/playlist?list=PLRUpXxWIqQmha-fY8rLBobP7Kbc3DdTvF&si=YFG2WyRsclC49k6s"
    ]

    result = subprocess.run(ydl_opts, capture_output=True, text=True)

    if result.returncode == 0:
        for line in result.stdout.strip().split("\n"):  # Procesa cada línea JSON
            info = json.loads(line)
            video_id = info.get("id")
            playlist.append({
                "title": info.get("title"),
                "url": f"https://www.youtube.com/watch?v={info.get('id')}",
                "vlcurl": None,
                "thumbnail": get_thumbnail(video_id),
            })


def shuffle_playlist():
    global Current, playlist, paused
    paused = True
    shuffle(playlist)
    Current = -1
    preload_song()


def get_audio_url(video_url) -> "vlc.MediaPlayer":
    ydl_opts = [
        "python", "-m", "yt_dlp",
        "--quiet", "--no-warnings",
        "-f", "bestaudio[ext=webm]",
        "--print-json", video_url
    ]

    result = subprocess.run(ydl_opts, capture_output=True, text=True)

    if result.returncode == 0:
        info = json.loads(result.stdout)
        return info["url"]
    else:
        print("Error extracting URL:", result.stderr)
        return None


def play_song(url, i=0):
    try:
        global player, instance, paused, Current

        if player and instance:
            media = instance.media_new(url)
            player.set_media(media)
            player.play()
        while player.is_playing() == 0:
            pass
        paused = False
        Current += i
    except:
        i += 1
        if Current >= len(playlist) - 1:
            shuffle_playlist()
        url = get_audio_url(playlist[Current+i]["url"])
        playlist[Current+i]["vlcurl"] = url
        player.play_song(url, i)


def pause_song():
    global player, paused
    playing = player.is_playing()
    if playing == 1:
        player.pause()
        paused = True
        return 0
    return -1


def resume_song():
    global player, paused
    playing = player.is_playing()
    if playing == 0:
        player.play()
        paused = False
        return 0
    return -1


def next_song():
    global Current, playlist, paused
    paused = True
    if Current == len(playlist) - 1:
        shuffle_playlist()
    eliminar_archivos()
    Current += 1
    vlcurl = playlist[Current]['vlcurl']
    if vlcurl:
        url = vlcurl
    else:
        url = playlist[Current]['url']
        url = get_audio_url(url)
        playlist[Current]['vlcurl'] = url
    play_song(url)
    return 0


def previous_song():
    global Current, playlist, paused, player, instance
    paused = True
    if Current == 0:
        return "no previous song"
    eliminar_archivos()
    Current -= 1
    vlcurl = playlist[Current]['vlcurl']
    if vlcurl:
        url = vlcurl
    else:
        url = playlist[Current]['url']
        url = get_audio_url(url)
        playlist[Current]['vlcurl'] = url
    try:
        if player and instance:
            media = instance.media_new(url)
            player.set_media(media)
            player.play()
        while player.is_playing() == 0:
            pass
        paused = False
    except:
        previous_song()


def preload_song():
    global Current, playlist
    if Current == len(playlist) - 1:
        shuffle_playlist()

    vlcurl = playlist[Current+1]['vlcurl']
    if vlcurl:
        return

    url = playlist[Current+1]['url']
    playlist[Current+1]['vlcurl'] = get_audio_url(url)
    eliminar_archivos()


def get_current_song():
    global Current, playlist
    if playlist and 0 <= Current < len(playlist):
        return playlist[Current]["title"], playlist[Current]["thumbnail"], Current
    return "No song playing"


def play_index_song(index):
    global Current, playlist, paused
    paused = True
    if index > len(playlist):
        return
    Current = index - 1
    data = {"id": 0}
    requests.post(url="http://127.0.0.1:5000/next", json=data)
    return 0


def play_random():
    global playlist
    num = randint(0, len(playlist) - 1)
    play_index_song(num)


def set_time_song(time):
    global player
    player.set_time(time)


def set_volume(level):
    global player
    player.audio_set_volume(level)


def get_thumbnail(video_id):
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"


def mains():
    global Current, playlist, paused, instance, player
    Current = 0
    instance = vlc.Instance()
    player = instance.media_player_new()
    data = {"id": 1}
    requests.post(url="http://127.0.0.1:5000/next", json=data)
    while True:
        playing = player.is_playing()
        if playing == 0 and not paused:
            print("hice un request :D")
            requests.post(url="http://127.0.0.1:5000/next", json=data)
            duration = 5
            sleep(duration)
