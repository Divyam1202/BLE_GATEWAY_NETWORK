from __future__ import annotations

import argparse
import json
import socket
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from packet_protocol import DATA_PACKET, END_PACKET, START_PACKET, Packet, decode_json_payload, hash_payload


@dataclass
class TransferState:
    metadata: dict
    total_packets: int
    remote_address: tuple[str, int]
    chunks: dict[int, bytes] = field(default_factory=dict)
    completion_info: dict | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase-2 Raspberry Pi server for receiving chunked packets from multiple clients."
    )
    parser.add_argument("--host", default="0.0.0.0", help="IP address to bind to.")
    parser.add_argument("--port", type=int, default=5000, help="TCP port to listen on.")
    parser.add_argument(
        "--output-dir",
        default="received_packets",
        help="Directory where completed client transfers are stored.",
    )
    return parser.parse_args()


def start_server(host: str, port: int, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"Phase-2 server listening on {host}:{port}")
        print(f"Saving received data under: {output_dir.resolve()}")

        while True:
            connection, address = server_socket.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(connection, address, output_dir),
                daemon=True,
            )
            thread.start()
            print(f"Accepted client connection from {address[0]}:{address[1]}")


def handle_client(connection: socket.socket, address: tuple[str, int], output_dir: Path) -> None:
    states: dict[str, TransferState] = {}

    with connection:
        while True:
            packet = Packet.from_socket(connection)
            if packet is None:
                print(f"Client disconnected: {address[0]}:{address[1]}")
                return

            transfer_key = packet.transfer_key

            if packet.packet_type == START_PACKET:
                metadata = decode_json_payload(packet)
                states[transfer_key] = TransferState(
                    metadata=metadata,
                    total_packets=packet.total_packets,
                    remote_address=address,
                )
                print(
                    f"Started transfer {transfer_key} from {metadata.get('client_id', 'unknown-client')} "
                    f"with {packet.total_packets} data packets."
                )
                continue

            state = states.get(transfer_key)
            if state is None:
                raise ValueError(f"Received packet for unknown transfer {transfer_key}")

            if packet.packet_type == DATA_PACKET:
                state.chunks[packet.packet_index] = packet.payload
                print(
                    f"Received chunk {packet.packet_index}/{packet.total_packets} "
                    f"for transfer {transfer_key}."
                )
                continue

            if packet.packet_type == END_PACKET:
                state.completion_info = decode_json_payload(packet)
                materialize_transfer(transfer_key, state, output_dir)
                states.pop(transfer_key, None)
                continue

            raise ValueError(f"Unsupported packet type: {packet.packet_type}")


def materialize_transfer(transfer_key: str, state: TransferState, output_dir: Path) -> None:
    expected_indexes = list(range(1, state.total_packets + 1))
    missing_indexes = [index for index in expected_indexes if index not in state.chunks]
    if missing_indexes:
        raise ValueError(f"Transfer {transfer_key} is missing packets: {missing_indexes}")

    payload = b"".join(state.chunks[index] for index in expected_indexes)
    completion_info = state.completion_info or {}

    if completion_info.get("total_bytes") is not None and completion_info["total_bytes"] != len(payload):
        raise ValueError(
            f"Transfer {transfer_key} reported {completion_info['total_bytes']} bytes but received {len(payload)}."
        )

    digest = hash_payload(payload)
    if completion_info.get("sha256") and completion_info["sha256"] != digest:
        raise ValueError(f"Transfer {transfer_key} failed checksum validation.")

    metadata = state.metadata
    client_id = metadata.get("client_id", "unknown-client")
    content_kind = metadata.get("content_kind", "message")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    client_dir = output_dir / client_id
    client_dir.mkdir(parents=True, exist_ok=True)

    if content_kind == "file":
        file_name = Path(metadata.get("name", f"{transfer_key}.bin")).name
        destination = client_dir / file_name
        destination.write_bytes(payload)
        print(f"Stored file transfer {transfer_key} at {destination}")
        return

    try:
        decoded_text = payload.decode(metadata.get("encoding", "utf-8"))
    except UnicodeDecodeError:
        decoded_text = payload.decode("utf-8", errors="replace")

    destination = client_dir / f"{timestamp}_{transfer_key}.txt"
    destination.write_text(decoded_text, encoding="utf-8")

    summary_path = client_dir / "messages.jsonl"
    with summary_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "transfer_id": transfer_key,
                    "client_id": client_id,
                    "received_from": f"{state.remote_address[0]}:{state.remote_address[1]}",
                    "content_kind": content_kind,
                    "bytes": len(payload),
                    "saved_to": str(destination),
                    "message": decoded_text,
                }
            )
        )
        handle.write("\n")

    print(f"Stored message transfer {transfer_key} at {destination}")
    print(f"Message from {client_id}: {decoded_text}")


if __name__ == "__main__":
    args = parse_args()
    start_server(args.host, args.port, Path(args.output_dir))
