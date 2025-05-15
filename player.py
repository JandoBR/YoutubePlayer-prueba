import subprocess
import requests
import webbrowser
from time import sleep
from pathlib import Path
from random import shuffle, randint
import yt_dlp
import vlc


player = None
instance = None
playlist = []
Current = 0
paused = False
BASE_URL = "http://127.0.0.1:5000"


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
    url = "https://youtube.com/playlist?list=PLRUpXxWIqQmha-fY8rLBobP7Kbc3DdTvF&si=fWU2UDGtXUPVtTmx"

    ydl_opts = {
        "quiet": True,  # Evita imprimir logs en la consola
        "extract_flat": True,  # No descarga los videos, solo obtiene la info
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=False)

    if result and "entries" in result:
        for entry in result["entries"]:
            video_id = entry.get("id")
            playlist.append({
                "title": entry.get("title"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "vlcurl": None,
                "thumbnail": get_thumbnail(video_id),
            })


def shuffle_playlist():
    global Current, playlist, paused
    paused = True
    shuffle(playlist)
    Current = -1


def get_audio_url(video_url) -> str:
    ydl_opts = {
        "quiet": True,  # Evita imprimir logs en consola
        "no_warnings": True,  # Suprime advertencias
        "format": "bestaudio[ext=webm]",  # Selecciona el mejor audio en WebM
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            return info["url"]
        except Exception as e:
            print("Error extracting URL:", e)
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
        if url:
            playlist[Current]['vlcurl'] = url
        else:
            return next_song()
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


# Variable auxiliar para almacenar temporalmente la última canción válida
last_known_info = ("No song playing", "", -1, None, None)


def get_current_song():
    global Current, playlist, player, last_known_info

    if playlist and 0 <= Current < len(playlist):
        title = playlist[Current]["title"]
        thumbnail = playlist[Current]["thumbnail"]

        if player:
            current_time = player.get_time() // 1000
            song_length = player.get_length() // 1000
            last_known_info = (title, thumbnail, Current,
                               current_time, song_length)
            return last_known_info

        last_known_info = (title, thumbnail, Current, None, None)
        return last_known_info

    # Si Current es -1 o la playlist está vacía, se devuelve la última canción conocida
    return last_known_info


def play_index_song(index):
    global Current, playlist, paused
    paused = True
    if index > len(playlist):
        return
    old = Current
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

# TODO


def menu_cli():
    # Esto abrirá http://localhost:5000 en el navegador predeterminado
    webbrowser.open("http://localhost:5000")


def mains():
    global Current, playlist, paused, instance, player
    instance = vlc.Instance()
    player = instance.media_player_new()
    data = {"id": 1}
    requests.post(url="http://127.0.0.1:5000/next", json=data)
    while True:
        sleep(0.5)
        if player.is_playing() == 0 and not paused:
            print("hice un request :D")
            requests.post(url="http://127.0.0.1:5000/next", json=data)
            sleep(5)
