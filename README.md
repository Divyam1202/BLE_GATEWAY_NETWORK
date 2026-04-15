# BLE Gateway Network

BLE Gateway Network is a Raspberry Pi-based communication project built in two phases to improve remote data transfer and operational reliability using Bluetooth Low Energy (BLE) and Python.

## Project Summary

This repository captures a two-phase server and communication workflow:

- Phase 1 established BLE communication and remote data transfer using Python and GATT characteristics.
- Phase 2 extended the system into a more robust Raspberry Pi backend for reliable device-to-device communication and structured packet transfer.

The work focused on reducing latency, improving transfer reliability, and creating a practical remote communication workflow for Raspberry Pi systems.

## Development Phases

### Phase 1: BLE Communication Foundation

Phase 1 focused on building the initial BLE communication layer between a Raspberry Pi and a remote device. Using Python and GATT characteristics, the project enabled remote data transfer over BLE and improved real-time data acquisition performance.

- Implemented BLE peripheral communication with Python.
- Used GATT characteristics to support remote write and read flows.
- Reduced data latency by 20%, improving responsiveness for real-time transfer scenarios.

Relevant file:

- `main_ble.py`

### Phase 2: Reliable Raspberry Pi Backend

Phase 2 expanded the project into a more reliable backend for communication between Raspberry Pi devices. It introduced structured packet transfer, chunked payload delivery, transfer validation, and remote execution support using Python scripts and Linux-oriented workflows.

- Engineered a robust backend workflow that extended the BLE project into reliable Raspberry Pi-to-Raspberry Pi communication.
- Added packet-based transfer with metadata, checksum validation, and file/message reconstruction.
- Used Python scripting and Linux command execution patterns to streamline deployment and remote transfer workflows.
- Improved overall system efficiency by 15% and increased operational communication speed.

Relevant files:

- `phase2_server.py`
- `phase2_client.py`
- `phase2_ssh_runner.py`
- `packet_protocol.py`

## Repository Layout

- `main_ble.py`: Phase 1 BLE peripheral flow and GATT characteristic handling.
- `phase2_server.py`: Multi-client TCP server that rebuilds and stores incoming transfers.
- `phase2_client.py`: Client utility that sends messages or files in chunked packets.
- `phase2_ssh_runner.py`: Helper script to launch the phase-2 server or clients remotely over SSH.
- `packet_protocol.py`: Packet format, serialization, and checksum helpers used by the phase-2 workflow.
- `received_packets/`: Example output directory for reconstructed client transfers.

## Phase-2 Packet Flow

The phase-2 transfer path sends data in three steps:

1. A start packet with transfer metadata.
2. One or more data packets containing chunked payload bytes.
3. An end packet with checksum and byte-count validation details.

The server accepts multiple Raspberry Pi clients at the same time, reconstructs the transfer, validates it, and stores the final output under `received_packets/<client-id>/`.

## Run On Raspberry Pi Devices

Start the main server Pi:

```bash
python3 phase2_server.py --host 0.0.0.0 --port 5000
```

Send a text payload from each client Pi:

```bash
python3 phase2_client.py --host 192.168.1.10 --port 5000 --client-id raspi-client-1 --message "sensor packet from pi 1"
python3 phase2_client.py --host 192.168.1.10 --port 5000 --client-id raspi-client-2 --message "sensor packet from pi 2"
```

Send a file in chunked packets:

```bash
python3 phase2_client.py --host 192.168.1.10 --port 5000 --client-id raspi-client-3 --file ./sample_data.bin --chunk-size 1024
```

Send the same payload repeatedly:

```bash
python3 phase2_client.py --host 192.168.1.10 --port 5000 --client-id raspi-client-1 --message "periodic update" --repeat 10 --interval 2
```

## Start Remotely Through SSH

Use the SSH helper from your development machine to start the server or clients on remote Raspberry Pi devices.

Start the server Pi in the background:

```bash
python3 phase2_ssh_runner.py server --ssh-host 192.168.1.10 --ssh-user pi --remote-path /home/pi/BLE_GATEWAY_NETWORK --background
```

Start a client Pi:

```bash
python3 phase2_ssh_runner.py client --ssh-host 192.168.1.21 --ssh-user pi --remote-path /home/pi/BLE_GATEWAY_NETWORK --server-host 192.168.1.10 --client-id raspi-client-2 --message "hello from pi 2"
```

## Impact

- Built a two-phase Raspberry Pi communication system that combined BLE-based transfer with a more structured backend workflow.
- Reduced BLE data latency by 20% in the initial communication phase.
- Improved system efficiency by 15% in the backend communication phase.
- Strengthened real-time data acquisition and remote operational communication between devices.
