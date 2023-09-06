import datetime
import pickle
from pathlib import Path

from RSD import config
from RSD import player

crons = []  # type: list[tuple[str, str]]

def init_cron():
    print("STARTING CRONS")
    pickle_path = Path(config.CONFIG_DIR_PATH) / "crons.pickle"
    if pickle_path.is_file():
        with pickle_path.open("rb") as f:
            new_crons = pickle.load(f)
            for cron in new_crons:
                crons.append(cron)
    run_scheduled_tasks()


def run_scheduled_tasks() -> None:
    print("RUNNING CRON")
    time_now = datetime.datetime.now().strftime("%H:%M")
    print(time_now)
    for (time, playlist) in crons[:]:
        if time.lstrip("0") == time_now.lstrip("0"):
            mpd.play_playlist(playlist)
            crons.remove((time, playlist))
    with open(Path(config.CONFIG_DIR_PATH) / "crons.pickle", "wb") as f:
        pickle.dump(crons, f)


async def clear_crons():
    global crons
    crons = []


async def delete_crons(time: str):
    global crons
    crons = [cron for cron in crons if cron[0].lstrip("0") != time.lstrip("0")]
