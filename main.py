from pathlib import Path
import json
from fastapi import Request
from nicegui import ui, app
import datetime
from typing import Any, Iterable

from RSD import config, player, presets, generated_config
from RSD.models import PlayRequest, PlayRequestTTSItem, PlayRequestAudioItem


if not app.storage.general.get('history'):
    app.storage.general['history'] = []

if not app.storage.general.get('schedule'):
    app.storage.general['schedule'] = {}


notification_message = ""
notification_type = ""
NOTIFY_CMD = "INCOMING COMMAND..."


def update_ui():
    global notification_message
    if notification_message:
        ui.notify(notification_message, type=notification_type or "info")
        notification_message = ""  # Clear the message after notifying


@app.post('/command')
async def command(request: Request):
    def now_str() -> str:
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    def modify_items_add_paths(items: Iterable[dict[str, Any]]) -> None:
        for item in items:
            if item["type"] == "tts":
                item["background_path"] = generated_config.AUDIOS[item["background_path"]]
            if item["type"] == "audio":
                item["path"] = generated_config.AUDIOS[item["path"]]


    json_data = await request.json()
    modify_items_add_paths(json_data["items"])
    print(json_data, flush=True)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>....", flush=True)

    global notification_message
    notification_message = NOTIFY_CMD

    prepared_play_request = PlayRequest.from_dict(json_data)
    file_url = await prepared_play_request.get_urls()

    file_url = [x for x, y in zip(file_url, json_data["items"]) if y["type"] == "tts"]
    # Immediately invoked hlaseni
    # player.play_playlist(file_url)

    print("Time now: ", now_str(), flush=True)
    delay = prepared_play_request.delay_s
    now = datetime.datetime.now()
    time = now + datetime.timedelta(seconds=delay)
    time = time + datetime.timedelta(minutes=1) if time.second != 0 else time
    print("Time with delay: ", time, flush=True)

    time = time.strftime('%H:%M')
    app.storage.general['schedule'][time] = (prepared_play_request.summary(), prepared_play_request.to_dict())
    schedule_ui.refresh()
    return {"status": "success", "received": json_data, "tts_file": file_url}


@ui.page('/')
def index():
    async def play_request(request):
        ui.notify("Loading...", type="info")
        player.play_playlist(await request.get_urls())
        app.storage.general['history'].insert(0, (f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}: {request.summary()}", request.to_dict()))
        history_loader.refresh()

    async def save_request_as_draft(request):
        app.storage.general['history'].insert(0, (f"[DRAFT] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}: {request.summary()}", request.to_dict()))
        history_loader.refresh()
        ui.notify("Saved draft to history", type="positive")

    prepared_play_request = PlayRequest.from_dict(presets.DEFAULT_PLAY_REQUEST.to_dict())

    def check_notifications():
        global notification_message
        if notification_message:
            update_ui()

    ui.timer(0.1, check_notifications)

    def replace_prepared_play_request(new_request_dict):
        nonlocal prepared_play_request
        prepared_play_request = PlayRequest.from_dict(new_request_dict)
        play_request_form.refresh()

    audio_options = {path.resolve(): path.stem for path in sorted(config.AUDIO_PATH.glob("*.*"))}
    background_options = {None: "No background"} | {path.resolve(): path.stem.capitalize() for path in sorted(config.BACKGROUND_PATH.glob("*.*"))}
    voice_options = [model for model in config.VOICE_MODELS.keys()]

    ui.query('.nicegui-content').classes('max-w-[800px] m-auto')

    # Header
    with ui.row().classes('w-full flex flex-row items-center'):
        ui.markdown("# 🤖 RSD").classes('mr-auto')

        @ui.refreshable
        def draw_status_icon():
            if prepared_play_request.pending:
                icon, color, label = 'pending', 'yellow', 'PROCESSING'
            elif player.is_playing():
                icon, color, label = 'play_circle', 'red', 'PLAYING'
            else:
                icon, color, label = 'check_circle', 'green', 'READY'

            with ui.row().classes('items-center'):
                ui.icon(name=icon, color=color).classes('text-2xl m-2 mr-0')
                ui.label(label).classes('m-2 ml-0')
                if label == 'PLAYING':
                    ui.button(icon='stop', color="dark", on_click=lambda: player.stop())

        draw_status_icon()
        ui.timer(1, lambda: draw_status_icon.refresh())


    # Toolbar
    with ui.row().classes('w-full flex flex-row items-center mb-8'):
        # History loader
        @ui.refreshable
        def history_loader():
            ui.icon(name='history').classes('text-2xl')

            def load_history():
                if history_select.value is not None:
                    replace_prepared_play_request(app.storage.general['history'][history_select.value][1])

            history_select = ui.select(
                options={
                    i: summary
                    for i, (summary, data) in enumerate(app.storage.general['history'])
                },
                value=None,
                with_input=True,
                on_change=load_history
            )

        history_loader()
        
        # Quick access
        
        def load_preset(preset_request):
            replace_prepared_play_request(preset_request.to_dict())
            ui.notify(f"Loaded quick access entry", type="positive")

        with ui.row().classes('items-center ml-auto'):
            for icon, request in presets.QUICK_ACCESS.items():
                ui.button(icon=icon, on_click=lambda request=request: load_preset(request))

    # Request creation form
    with ui.column().classes('w-full'):
        @ui.refreshable
        def play_request_form():
            for i, item in enumerate(prepared_play_request.items):
                if isinstance(item, PlayRequestAudioItem):
                    play_request_audio_item_form(i, item)
                elif isinstance(item, PlayRequestTTSItem):
                    play_request_tts_item_form(i, item)

        def play_request_audio_item_form(i: int, item: PlayRequestAudioItem):
            with ui.card().classes('w-full my-2'), ui.row().classes('w-full'):
                ui.icon('audiotrack').classes('text-5xl p-2')
                ui.select(options=audio_options).bind_value(item, 'path').classes('block grow')
                request_audio_item_buttons(i)

        def play_request_tts_item_form(i: int, item: PlayRequestTTSItem):
            with ui.card().classes('w-full my-2'), ui.row().classes('w-full'):
                ui.icon('record_voice_over').classes('text-5xl p-2')
                with ui.column().classes('grow'):
                    ui.textarea().bind_value(item, 'text').classes('w-full')
                    with ui.row().classes('w-full items-center'):
                        ui.icon('music_note').classes('text-2xl')
                        ui.select(options=background_options).bind_value(item, 'background_path').classes('grow')
                    with ui.row().classes('w-full items-center'):
                        ui.icon('record_voice_over').classes('text-2xl')
                        ui.select(options=voice_options).bind_value(item, 'voice_model').classes('grow')
                    with ui.row().classes('w-full items-center'):
                        ui.icon('repeat').classes('text-2xl')
                        ui.toggle(options={False: "1×", True: "2×"}).bind_value(item, 'repeat')
                request_audio_item_buttons(i)

        def request_audio_item_buttons(i: int):
            with ui.column():
                def delete():
                    prepared_play_request.items.pop(i)
                    play_request_form.refresh()
                ui.button(icon='delete', color='dark', on_click=delete)

                if i > 0:
                    def move_up():
                        prepared_play_request.items[i], prepared_play_request.items[i-1] = prepared_play_request.items[i-1], prepared_play_request.items[i]
                        play_request_form.refresh()
                    ui.button(icon='arrow_upward', color='dark', on_click=move_up)

                if i < len(prepared_play_request.items) - 1:
                    def move_down():
                        prepared_play_request.items[i], prepared_play_request.items[i+1] = prepared_play_request.items[i+1], prepared_play_request.items[i]
                        play_request_form.refresh()
                    ui.button(icon='arrow_downward', color='dark', on_click=move_down)

        play_request_form()

        with ui.row().classes('w-full flex flex-row items-stretch mt-4'):
            with ui.row().classes('mr-auto'):
                ui.button(icon='audiotrack', text='+ audio', color='dark', on_click=lambda: (prepared_play_request.items.append(PlayRequestAudioItem()), play_request_form.refresh())).classes('h-full inline-block')
                ui.button(icon='record_voice_over', text='+ TTS', color='dark', on_click=lambda: (prepared_play_request.items.append(PlayRequestTTSItem()), play_request_form.refresh())).classes('h-full inline-block')

            with ui.row():
                ui.button(icon='save', color='dark', on_click=lambda: save_request_as_draft(prepared_play_request)).classes('inline-block').classes('text-xl')

                async def save_request_to_schedule():
                    time = time_picker.value
                    if time in app.storage.general['schedule']:
                        ui.notify(f"Schedule at {time} already exists! Remove it first.", type="negative")
                        return
                    time_picker_dialog.close()
                    ui.notify(f"Scheduled at {time}, processing...", type="positive")
                    await prepared_play_request.get_urls()
                    app.storage.general['schedule'][time] = (prepared_play_request.summary(), prepared_play_request.to_dict())
                    schedule_ui.refresh()

                with ui.dialog() as time_picker_dialog, ui.card():
                    time_picker = ui.time().props(add='format24h')
                    ui.button(icon='save', text='save to schedule', on_click=save_request_to_schedule).classes('w-full')

                ui.button(icon='more_time', on_click=time_picker_dialog.open).classes('inline-block').classes('text-xl')
                ui.button(icon='play_arrow', text='play', on_click=lambda: play_request(prepared_play_request)).classes('inline-block').classes('text-xl')

        schedule_ui()


@ui.refreshable
def schedule_ui():
    with ui.column().classes('w-full mt-8') as schedule:
        ui.markdown('## Schedule')
        now_time = datetime.datetime.now().strftime('%H:%M')
        schedule_items_sorted = sorted(app.storage.general['schedule'].items())
        schedule_items_sorted_before_now = [item for item in schedule_items_sorted if item[0] < now_time]
        schedule_items_sorted_after_now = [item for item in schedule_items_sorted if item[0] >= now_time]

        for time, (summary, data) in (schedule_items_sorted_after_now + schedule_items_sorted_before_now):
            with ui.card().classes('w-full'), ui.row().classes('w-full items-start'):
                ui.label(time).classes('block text-2xl')
                ui.html(summary).classes('block grow w-0')

                with ui.column():
                    def remove_from_schedule(time):
                        app.storage.general['schedule'].pop(time)
                        schedule_ui.refresh()

                    ui.button(icon='delete', color='dark', on_click=lambda time=time: remove_from_schedule(time))

                    def edit_request(time):
                        (summary, data) = app.storage.general['schedule'].pop(time)
                        # nonlocal prepared_play_request
                        global prepared_play_request
                        prepared_play_request = PlayRequest.from_dict(data)
                        play_request_form.refresh()
                        schedule_ui.refresh()
                        ui.notify("Unscheduled and loaded into editor", type="positive")

                    ui.button(icon='edit', color='dark', on_click=lambda time=time: edit_request(time)).classes('block ml-auto')

        if not schedule_items_sorted:
            ui.label('(nothing is scheduled)').classes('text-xl')


async def play_scheduled():
    time_now = datetime.datetime.now().strftime('%H:%M')
    entry = app.storage.general['schedule'].pop(time_now, None)
    if entry is None:
        return
    summary, data = entry
    request = PlayRequest.from_dict(data)
    player.play_playlist(await request.get_urls())
    app.storage.general['history'].insert(0, (f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}: {request.summary()}", request.to_dict()))

ui.timer(10, play_scheduled)


async def cleanup_tts():
    paths_not_recent = {
        str(path.resolve())
        for path in config.TTS_PATH.glob('tts_*.wav')
        if datetime.datetime.fromtimestamp(path.stat().st_mtime) < datetime.datetime.now() - datetime.timedelta(days=1)
    }
    paths_used_in_schedule = {
        path
        for (_, data) in app.storage.general['schedule'].values()
        for path in await PlayRequest.from_dict(data).get_urls()
    }
    paths_to_delete = paths_not_recent - paths_used_in_schedule
    for path in paths_to_delete:
        Path(path).unlink()

ui.timer(3600, cleanup_tts)


ui.run(title="RSD", favicon="🤖", dark=True, show=False, port=8080)
