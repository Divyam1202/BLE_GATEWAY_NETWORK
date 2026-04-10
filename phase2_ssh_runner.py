from __future__ import annotations

import argparse
import shlex
import subprocess


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the phase-2 Raspberry Pi server or clients remotely over SSH."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    server_parser = subparsers.add_parser("server", help="Start the phase-2 server on a remote Raspberry Pi.")
    add_common_ssh_args(server_parser)
    server_parser.add_argument("--listen-host", default="0.0.0.0", help="Bind address for the remote server.")
    server_parser.add_argument("--listen-port", type=int, default=5000, help="Bind port for the remote server.")
    server_parser.add_argument("--output-dir", default="received_packets", help="Where the remote server saves data.")

    client_parser = subparsers.add_parser("client", help="Start a phase-2 client on a remote Raspberry Pi.")
    add_common_ssh_args(client_parser)
    client_parser.add_argument("--server-host", required=True, help="IP or hostname of the main server Pi.")
    client_parser.add_argument("--server-port", type=int, default=5000, help="TCP port of the main server Pi.")
    client_parser.add_argument("--client-id", required=True, help="Client identifier used in packet metadata.")
    client_parser.add_argument("--chunk-size", type=int, default=512, help="Payload size per packet.")
    client_parser.add_argument("--repeat", type=int, default=1, help="How many times to send the payload.")
    client_parser.add_argument("--interval", type=float, default=0.0, help="Delay between repeated transfers.")

    source_group = client_parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--message", help="Message payload to send from the remote client.")
    source_group.add_argument("--file", help="Path to a file on the remote Raspberry Pi to send.")

    return parser.parse_args()


def add_common_ssh_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ssh-host", required=True, help="SSH hostname or IP of the Raspberry Pi.")
    parser.add_argument("--ssh-user", default="pi", help="SSH username for the Raspberry Pi.")
    parser.add_argument(
        "--remote-path",
        default="~/BLE_GATEWAY_NETWORK",
        help="Path to the project on the remote Raspberry Pi.",
    )
    parser.add_argument("--python-bin", default="python3", help="Python interpreter to use remotely.")
    parser.add_argument(
        "--background",
        action="store_true",
        help="Run the remote command with nohup so it keeps running after SSH exits.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the SSH command without executing it.",
    )


def build_remote_command(args: argparse.Namespace) -> str:
    if args.mode == "server":
        script_parts = [
            args.python_bin,
            "phase2_server.py",
            "--host",
            args.listen_host,
            "--port",
            str(args.listen_port),
            "--output-dir",
            args.output_dir,
        ]
    else:
        script_parts = [
            args.python_bin,
            "phase2_client.py",
            "--host",
            args.server_host,
            "--port",
            str(args.server_port),
            "--client-id",
            args.client_id,
            "--chunk-size",
            str(args.chunk_size),
            "--repeat",
            str(args.repeat),
            "--interval",
            str(args.interval),
        ]
        if args.message is not None:
            script_parts.extend(["--message", args.message])
        if args.file is not None:
            script_parts.extend(["--file", args.file])

    project_command = f"cd {shlex.quote(args.remote_path)} && {shlex.join(script_parts)}"
    if not args.background:
        return project_command

    log_name = "phase2_server.log" if args.mode == "server" else f"{args.client_id}.log"
    return f"cd {shlex.quote(args.remote_path)} && nohup {shlex.join(script_parts)} > {shlex.quote(log_name)} 2>&1 &"


def execute_ssh(args: argparse.Namespace) -> None:
    remote_command = build_remote_command(args)
    ssh_command = ["ssh", f"{args.ssh_user}@{args.ssh_host}", remote_command]

    if args.dry_run:
        print(" ".join(shlex.quote(part) for part in ssh_command))
        return

    subprocess.run(ssh_command, check=True)


if __name__ == "__main__":
    execute_ssh(parse_args())
