import json
import socket
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class Device:
    id: str
    ip: str
    name: str
    is_connected: bool
    is_muted: bool
    volume: int


def make_device(**kwargs) -> Device:
    id = kwargs["id"]
    ip = kwargs["ip"]
    name = kwargs["name"]
    is_connected = kwargs["conn"]
    is_muted = kwargs["mute"]
    vol = int(kwargs["vol"])
    return Device(id, ip, name, is_connected, is_muted, vol)


def send_jsonrpc_request(host: str, port: int, method, params=None) -> Any:
    request = {"id": 1, "jsonrpc": "2.0", "method": method}
    response = None
    if params:
        request["params"] = params

    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            request_str = json.dumps(request)
            print(f"Sending request: {request_str}")
            sock.sendall(request_str.encode() + b"\n")
            response = sock.recv(4096).decode()
            print(f"Received response: {response}")
        return json.loads(response)
    except socket.error as e:
        print(f"Socket error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw response: {response}")
        sys.exit(1)


def list_clients(host: str = "localhost", port: int = 1780) -> list[Device]:
    response = None
    try:
        response = send_jsonrpc_request(host, port, "Server.GetStatus")

        if "result" not in response:
            print("Error: Unexpected response from Snapserver")
            return []

        groups = response["result"]["server"]["groups"]

        for group in groups:
            for client in group["clients"]:
                print(client["config"]["volume"], flush=True)

        devices = [make_device(
            id=client["id"],
            ip=client["host"]["ip"],
            name=client["host"]["name"],
            conn=client["connected"],
            mute=client["config"]["volume"]["muted"],
            vol=client["config"]["volume"]["percent"],
        ) for group in groups for client in group["clients"]]

        return devices

    except KeyError as e:
        print(f"Error: Unexpected response structure. Missing key: {e}")
        print(f"Full response: {response}")
        return []


def get_connected_clients(host: str, port: int) -> list[Device]:
    clients = list_clients(host, port)
    return [client for client in clients if client.is_connected]


if __name__ == "__main__":
    if len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
        print(list_clients(host, port))
    elif len(sys.argv) == 1:
        print(list_clients())
    else:
        print("Usage: python script.py [host] [port]")
        print("If no arguments are provided, defaults to localhost:1780")
        sys.exit(1)
