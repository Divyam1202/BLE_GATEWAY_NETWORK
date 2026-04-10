from __future__ import annotations

import argparse
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

from packet_protocol import create_packets, send_packets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase-2 Raspberry Pi client that sends chunked payloads to the server."
    )
    parser.add_argument("--host", required=True, help="Server IP or hostname.")
    parser.add_argument("--port", type=int, default=5000, help="Server TCP port.")
    parser.add_argument("--client-id", required=True, help="Readable client identifier, for example raspi-client-1.")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Payload size per packet in bytes.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of times to send the payload over the same connection.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.0,
        help="Delay in seconds between repeated transfers.",
    )

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--message", help="Text message to send to the phase-2 server.")
    source_group.add_argument("--file", help="Path to a file that should be sent in packets.")
    source_group.add_argument(
        "--stdin",
        action="store_true",
        help="Read the payload from standard input instead of the command line.",
    )

    return parser.parse_args()


def load_payload(args: argparse.Namespace) -> tuple[bytes, dict]:
    timestamp = datetime.now().isoformat(timespec="seconds")

    if args.file:
        path = Path(args.file)
        payload = path.read_bytes()
        metadata = {
            "client_id": args.client_id,
            "content_kind": "file",
            "name": path.name,
            "encoding": "binary",
            "timestamp": timestamp,
        }
        return payload, metadata

    if args.stdin:
        payload = sys.stdin.read().encode("utf-8")
        metadata = {
            "client_id": args.client_id,
            "content_kind": "message",
            "name": "stdin-message.txt",
            "encoding": "utf-8",
            "timestamp": timestamp,
        }
        return payload, metadata

    payload = args.message.encode("utf-8")
    metadata = {
        "client_id": args.client_id,
        "content_kind": "message",
        "name": "message.txt",
        "encoding": "utf-8",
        "timestamp": timestamp,
    }
    return payload, metadata


def send_transfer(host: str, port: int, payload: bytes, metadata: dict, chunk_size: int) -> None:
    packets = create_packets(payload=payload, metadata=metadata, chunk_size=chunk_size)
    transfer_id = packets[0].transfer_key

    with socket.create_connection((host, port)) as connection:
        send_packets(connection, packets)

    packet_count = len(packets) - 2
    print(
        f"Sent transfer {transfer_id} "
        f"from {metadata['client_id']} as {packet_count} data packets."
    )


if __name__ == "__main__":
    arguments = parse_args()
    payload_bytes, base_metadata = load_payload(arguments)

    for iteration in range(1, arguments.repeat + 1):
        metadata = dict(base_metadata)
        metadata["iteration"] = iteration
        send_transfer(
            host=arguments.host,
            port=arguments.port,
            payload=payload_bytes,
            metadata=metadata,
            chunk_size=arguments.chunk_size,
        )

        if iteration < arguments.repeat and arguments.interval > 0:
            time.sleep(arguments.interval)
