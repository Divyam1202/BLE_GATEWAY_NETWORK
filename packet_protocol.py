from __future__ import annotations

import hashlib
import json
import math
import socket
import struct
import uuid
from dataclasses import dataclass
from typing import Iterable


MAGIC = b"BGW1"
START_PACKET = 1
DATA_PACKET = 2
END_PACKET = 3
HEADER_STRUCT = struct.Struct("!4sB16sIIH")


@dataclass
class Packet:
    packet_type: int
    transfer_id: bytes
    packet_index: int
    total_packets: int
    payload: bytes

    def to_bytes(self) -> bytes:
        header = HEADER_STRUCT.pack(
            MAGIC,
            self.packet_type,
            self.transfer_id,
            self.packet_index,
            self.total_packets,
            len(self.payload),
        )
        return header + self.payload

    @classmethod
    def from_socket(cls, connection: socket.socket) -> "Packet | None":
        header = _recv_exact(connection, HEADER_STRUCT.size)
        if header is None:
            return None

        magic, packet_type, transfer_id, packet_index, total_packets, payload_length = HEADER_STRUCT.unpack(header)
        if magic != MAGIC:
            raise ValueError("Unexpected packet header received.")

        payload = _recv_exact(connection, payload_length)
        if payload is None:
            raise ConnectionError("Connection closed before payload was fully received.")

        return cls(
            packet_type=packet_type,
            transfer_id=transfer_id,
            packet_index=packet_index,
            total_packets=total_packets,
            payload=payload,
        )

    @property
    def transfer_key(self) -> str:
        return self.transfer_id.hex()


def create_packets(payload: bytes, metadata: dict, chunk_size: int) -> list[Packet]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    total_packets = max(1, math.ceil(len(payload) / chunk_size))
    transfer_id = uuid.uuid4().bytes
    metadata = dict(metadata)
    metadata.setdefault("transfer_id", transfer_id.hex())
    metadata.setdefault("total_bytes", len(payload))

    packets = [
        Packet(
            packet_type=START_PACKET,
            transfer_id=transfer_id,
            packet_index=0,
            total_packets=total_packets,
            payload=json.dumps(metadata).encode("utf-8"),
        )
    ]

    if payload:
        for packet_index, start in enumerate(range(0, len(payload), chunk_size), start=1):
            chunk = payload[start : start + chunk_size]
            packets.append(
                Packet(
                    packet_type=DATA_PACKET,
                    transfer_id=transfer_id,
                    packet_index=packet_index,
                    total_packets=total_packets,
                    payload=chunk,
                )
            )
    else:
        packets.append(
            Packet(
                packet_type=DATA_PACKET,
                transfer_id=transfer_id,
                packet_index=1,
                total_packets=total_packets,
                payload=b"",
            )
        )

    packets.append(
        Packet(
            packet_type=END_PACKET,
            transfer_id=transfer_id,
            packet_index=total_packets + 1,
            total_packets=total_packets,
            payload=json.dumps(
                {
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "total_bytes": len(payload),
                }
            ).encode("utf-8"),
        )
    )

    return packets


def send_packets(connection: socket.socket, packets: Iterable[Packet]) -> None:
    for packet in packets:
        connection.sendall(packet.to_bytes())


def decode_json_payload(packet: Packet) -> dict:
    return json.loads(packet.payload.decode("utf-8"))


def hash_payload(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _recv_exact(connection: socket.socket, length: int) -> bytes | None:
    buffer = bytearray()
    while len(buffer) < length:
        chunk = connection.recv(length - len(buffer))
        if not chunk:
            if not buffer:
                return None
            raise ConnectionError("Connection closed before enough bytes were received.")
        buffer.extend(chunk)
    return bytes(buffer)
