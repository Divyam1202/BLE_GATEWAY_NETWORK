# BLE Gateway Network

BLE Gateway Network is a Raspberry Pi communication project built to explore low-latency Bluetooth Low Energy workflows and reliable remote data transfer between devices. The repository combines an initial BLE GATT prototype with a second-phase packet-based backend for Raspberry Pi-to-Raspberry Pi communication.

## Overview

This project was developed in two phases:

### Phase 1: BLE Communication Prototype

The first phase focused on establishing Bluetooth Low Energy communication using Python and GATT characteristics on Raspberry Pi. The goal was to create a lightweight path for remote command or data exchange over BLE.

- Implemented a custom BLE service using `bluez_peripheral`.
- Defined GATT characteristics for write and notify/read interactions.
- Built the foundation for remote data transfer and real-time acquisition workflows.
- Project results were measured as a 20% reduction in data latency during the BLE-focused phase.

### Phase 2: Raspberry Pi Network Backend

The second phase extended the idea beyond direct BLE interaction into a more robust backend that supports structured packet transfer between Raspberry Pi devices. This phase adds transfer metadata, chunking, checksum validation, and remote launch utilities for multi-device setups.

- Implemented packetized file and message transfer between Raspberry Pi systems.
- Added a threaded server to receive and reconstruct client transfers.
- Introduced transfer validation using byte counts and SHA-256 checksums.
- Added SSH helpers to launch server and client processes remotely.
- Project results were measured as a 15% improvement in system efficiency during the backend communication phase.

## Key Features

- Custom BLE service and GATT characteristic handling in Python
- Chunked packet transfer for messages and files
- Multi-client TCP server for Raspberry Pi communication
- Metadata-aware transfer tracking
- Integrity validation with SHA-256 hashing
- Remote orchestration with SSH
- Clean separation between BLE experimentation and networked backend workflows

## Repository Structure

- `main_ble.py`: Phase 1 BLE service implementation using GATT characteristics.
- `packet_protocol.py`: Shared packet format, serialization, parsing, and checksum helpers.
- `phase2_server.py`: Multi-client server that receives, validates, and stores transfers.
- `phase2_client.py`: Client utility for sending messages or files in chunks.
- `phase2_ssh_runner.py`: SSH wrapper for starting the phase-2 server or clients on remote Raspberry Pi devices.
- `received_packets/`: Output directory where reconstructed transfers are stored.

## How Phase 2 Works

Each transfer is sent in three parts:

1. A start packet containing metadata such as client identity and content details.
2. One or more data packets containing the payload in chunks.
3. An end packet containing transfer completion details, including checksum and total byte count.

The server rebuilds the payload, validates it, and writes the result into a client-specific directory under `received_packets/`.

## Requirements

- Raspberry Pi devices running Linux
- Python 3
- Bluetooth support and BlueZ for BLE work
- The Python package used in phase 1:

```bash
pip install bluez-peripheral
```

## Running The Project

### Phase 1: Start the BLE Service

Run the BLE prototype on the Raspberry Pi:

```bash
python3 main_ble.py
```

This phase is intended for BLE communication experiments based on custom GATT characteristics.

### Phase 2: Start the Packet Server

Run the server on the main Raspberry Pi:

```bash
python3 phase2_server.py --host 0.0.0.0 --port 5000
```

### Phase 2: Send a Message From a Client Pi

```bash
python3 phase2_client.py --host 192.168.1.10 --port 5000 --client-id raspi-client-1 --message "sensor packet from pi 1"
```

### Phase 2: Send a File

```bash
python3 phase2_client.py --host 192.168.1.10 --port 5000 --client-id raspi-client-2 --file ./sample_data.bin --chunk-size 1024
```

### Phase 2: Run Repeated Transfers

```bash
python3 phase2_client.py --host 192.168.1.10 --port 5000 --client-id raspi-client-1 --message "periodic update" --repeat 10 --interval 2
```

## Remote Execution Over SSH

Start the server remotely:

```bash
python3 phase2_ssh_runner.py server --ssh-host 192.168.1.10 --ssh-user pi --remote-path /home/pi/BLE_GATEWAY_NETWORK --background
```

Start a client remotely:

```bash
python3 phase2_ssh_runner.py client --ssh-host 192.168.1.21 --ssh-user pi --remote-path /home/pi/BLE_GATEWAY_NETWORK --server-host 192.168.1.10 --client-id raspi-client-2 --message "hello from pi 2"
```

## Impact

- Reduced BLE-phase data latency by 20%
- Improved backend communication efficiency by 15%
- Created a clearer path from direct BLE interaction to scalable multi-device Raspberry Pi communication

## Future Improvements

- Add end-to-end automation between BLE ingestion and phase-2 packet forwarding
- Improve command parsing and execution safety in the BLE service
- Add tests for packet validation and transfer edge cases
- Add configuration files for multi-device deployment
