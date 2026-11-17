"""Read one aligned 32-bit RAM value through an existing OpenOCD session."""
import argparse
import csv
import socket
import struct
import time


def rpc(command):
    wrapper = 'set code [catch {' + command + '} data]; format "%d\\n%s" $code $data'
    with socket.create_connection(('127.0.0.1', 50001), timeout=5) as connection:
        connection.sendall(wrapper.encode('ascii') + b'\x1a')
        response = bytearray()
        while not response.endswith(b'\x1a'):
            part = connection.recv(4096)
            if not part:
                raise RuntimeError('OpenOCD closed the connection')
            response.extend(part)
            if len(response) > 65536:
                raise RuntimeError('Unexpectedly large RPC response')
    code, data = response[:-1].decode('utf-8').split('\n', 1)
    if code != '0':
        raise RuntimeError(data)
    return data.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--address', required=True, type=lambda value: int(value, 0))
    parser.add_argument('--type', choices=['i32', 'u32', 'f32'], default='f32')
    parser.add_argument('--samples', type=int, default=100)
    parser.add_argument('--interval', type=float, default=0.05)
    parser.add_argument('--output', default='capture.csv')
    args = parser.parse_args()
    if not 0x20000000 <= args.address <= 0x200FFFFC or args.address % 4:
        parser.error('Use an aligned RAM address confirmed for your STM32 and matching ELF')
    if args.samples < 1 or not 0 < args.interval <= 3600:
        parser.error('samples must be positive and interval must be in (0, 3600]')
    fmt = {'i32': '<i', 'u32': '<I', 'f32': '<f'}[args.type]
    with open(args.output, 'x', newline='', encoding='utf-8') as output:
        writer = csv.writer(output)
        writer.writerow(['host_elapsed_s', 'address', 'type', 'value'])
        start = time.monotonic()
        for index in range(args.samples):
            if rpc('stm32f1x.cpu curstate') != 'running':
                raise RuntimeError('Target is not running; no reset or resume will be issued')
            word = int(rpc(f'read_memory {args.address:#x} 32 1'), 0)
            value = struct.unpack(fmt, struct.pack('<I', word))[0]
            writer.writerow([time.monotonic() - start, hex(args.address), args.type, value])
            output.flush()
            if index + 1 < args.samples:
                time.sleep(max(0, start + (index + 1) * args.interval - time.monotonic()))
    print(f'Saved {args.samples} samples to {args.output}')


if __name__ == '__main__':
    main()
