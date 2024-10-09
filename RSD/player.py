import sys

from mpd import MPDClient
from snapcast.control import Snapserver
import snapcast
from snapcast.control.client import Snapclient
import asyncio
from ipaddress import IPv4Address as IPv4
from main import get_devices

from RSD import config

TargetSnapClients = list[str] | None
SnapClients = list[Snapclient] | None

mpd_client: MPDClient | None = None
snapserver: Snapserver | None = None


async def ensure_connected():
    global mpd_client
    global snapserver
    try:
        mpd_client.status()
        clients = snapserver.clients
        print("try clients: ", clients, flush=True)
    except:
        try:
            mpd_client = MPDClient()
            mpd_client.connect(str(config.MPD_SOCKET_PATH))

            loop = asyncio.get_event_loop()
            snapserver = await snapcast.control.create_server(
                loop, config.SNAPSERVER_HOST, port=config.SNAPSERVER_PORT
            )
            for client in snapserver.clients:
                client.set_callback(lambda c: print(f"""
                THIS IS CLIENT UPDATE CALLBACK
                
                {c.muted=}
                {c.volume=}
                """))

        except FileNotFoundError:
            print(f"ERROR: MPD socket at {config.MPD_SOCKET_PATH} not found. Is MPD running?", file=sys.stderr)
            sys.exit(1)
        except ConnectionError as e:
            print(f"ERROR: Can't connect to MPD ({e.message})", file=sys.stderr)
            sys.exit(1)


async def play_playlist(urls: list[str], target_clients: SnapClients = None):
    print(f"{target_clients=}", flush=True)
    if target_clients == []:
        return

    await ensure_connected()
    mpd_client.stop()
    mpd_client.clear()
    for url in urls:
        mpd_client.add(url)

    duration = sum([float(item['duration']) for item in mpd_client.playlistinfo()])

    clients = None
    if target_clients:
        clients = snapserver.clients

    print("CLIENTS>>>>>>>>>>>>>>>>>>>", [(x.muted, x.volume) for x in snapserver.clients], flush=True)
    await mute_clients(clients, target_clients)

    mpd_client.play()

    print("[  DURATION  ]: ", duration, flush=True)
    # print(f"MPD status after mute: {mpd_client.status()}", flush=True)
    await asyncio.sleep(float(duration) + 1.0)
    await unmute_clients(clients, target_clients)
    await unmute_clients(clients, target_clients) # not cleaning correctly withou this

async def stop():
    await ensure_connected()
    mpd_client.stop()
    mpd_client.clear()


async def is_playing():
    await ensure_connected()
    return mpd_client.status()['state'] == "play"


async def mute_clients(clients: SnapClients, target_clients: TargetSnapClients = None) -> None:
    if target_clients:
        for client in clients:
            if client.identifier not in target_clients:
                await client.set_muted(True)
                client.update_volume({'volume': {'muted': True, 'percent': 0}})
                await asyncio.sleep(1)
    print(f"MUTE: {get_devices()=}", flush=True)


async def unmute_clients(clients: SnapClients, target_clients: TargetSnapClients = None) -> None:
    if target_clients:
        for client in clients:
            await client.set_muted(False)
            client.update_volume({'volume': {'muted': False, 'percent': 100}})
            await asyncio.sleep(1)
    print(f"UNMUTE: {get_devices()=}", flush=True)
