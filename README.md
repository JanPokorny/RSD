# 🤖 RSD

> Robotický Správce Deace

A system with a web GUI to play songs and TTS utterances on multiple devices at once. Made for [Deace](http://dehydratace.chim.cz/).

## Features

- Play songs and TTS utterances on a network of synchronized devices (old phones / laptops, Raspberry Pis, etc.)
- Add background music to TTS voice
- Control what is played from anywhere using a web interface
- Schedule events for a specific time
- Browse and search the play history

At the current state, the system is tuned for using a Czech TTS voice and has quick access presets for alarm, playtime, lunch and dinner music.

![image](https://github.com/JanPokorny/RSD/assets/4580066/ea9fc6e0-1b0c-4fa2-9897-ee1ebd758cf9)

## How to run

### Preparation

The files in `data/audio` are just empty stubs, you need to replace them with actual audio files. Any format supported by `mpd` should work, not just MP3. (The files in `data/background` are real out of the box.)

The audio presets can be edited in `RSD/presets.py`.

### Server

Recommended: Ubuntu 22.04, everything else is _hic sunt leones_.

#### Install

```bash
sudo apt install -y mpd snapserver snapclient python3.11 python3.11-venv
sudo systemctl disable snapserver
sudo pkill snapserver
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

#### Run

```bash
.venv/bin/honcho start
```

Access the web interface on `http://<host IP>:8080`.

> **WARNING:** When first generating audio, the models need to be downloaded. This can take a while and the server will be unresponsive during that time.

> **TIP:** Use [ngrok](https://ngrok.com/) to expose the web interface to the internet and play songs from anywhere!

### Client

The clients connect to host IP on port 1704 (stream port) and 1705 (control port). The Android client has a "scan" feature so you don't have to type the IP manually.

#### Linux

Install `snapclient` and run:

```bash
snapclient -h <host IP>
```

#### Windows

Install and use the application [Snap.Net](https://github.com/stijnvdb88/snap.net).

#### Android

Install and use the application [Snapcast](https://play.google.com/store/apps/details?id=de.badaix.snapcast&hl=en_US&gl=US).

## FAQ

### How does the UI work?

It uses NiceGUI, which is a clever Python UI framework that automatically creates a Vue frontend for Python code, communicating through websockets. It's the exact kind of thing you would use for a project like this.

### Why does it take a few seconds to start/stop playing?

The file `conf/snapserver.conf` instructs the server to buffer 3s of audio before playing. This ensures smoother sync.

### Why does it sometimes skip a few seconds of audio?

When the connection is shitty and snapcast is unable to sync with the server, it will stay silent until it catches up. Not much else can be done other than improving the connection.
