# BLE Gateway Network

This repository now documents the project in two parts:

- `main_ble.py`: phase-1 BLE peripheral flow between the Raspberry Pi and a mobile phone.
- `phase2_server.py` and `phase2_client.py`: phase-2 Raspberry Pi to Raspberry Pi communication over TCP sockets using chunked packets.

## Phase-2 Packet Flow

The client script divides a message or file into fixed-size chunks and sends:

1. a start packet with metadata
2. one or more data packets
3. an end packet with checksum and byte count

The server script accepts multiple Raspberry Pi clients at the same time, rebuilds the transfer, validates it, and stores the result under `received_packets/<client-id>/`.

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

This gives you a simple 1-server / 2-to-3-client layout that extends the original BLE work into a second networked Raspberry Pi phase.
