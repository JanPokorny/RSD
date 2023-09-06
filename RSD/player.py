import sys

from mpd import MPDClient

from RSD import config

mpd_client: MPDClient | None = None


def ensure_connected():
    global mpd_client
    try:
        mpd_client.status()
    except:
        try:
            mpd_client = MPDClient()
            mpd_client.connect(str(config.MPD_SOCKET_PATH))
        except FileNotFoundError:
            print(f"ERROR: MPD socket at {config.MPD_SOCKET_PATH} not found. Is MPD running?", file=sys.stderr)
            sys.exit(1)
        except ConnectionError as e:
            print(f"ERROR: Can't connect to MPD ({e.message})", file=sys.stderr)
            sys.exit(1)


def play_playlist(urls: list[str]):
    ensure_connected()
    mpd_client.stop()
    mpd_client.clear()
    for url in urls:
        mpd_client.add(url)
    mpd_client.play()


def stop():
    ensure_connected()
    mpd_client.stop()
    mpd_client.clear()


def is_playing():
    ensure_connected()
    return mpd_client.status()['state'] == "play"
