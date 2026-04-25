import psutil
import subprocess
import re

from argparse import ArgumentParser
from .utils import progress_bar, format_bytes_compact
from .ascii_escape import *


locale = {
    'en': {
        'header': 'System Resource Monitor',
        'cpu': 'CPU usage',
        'ram': 'RAM usage',
        'disk': 'Disk usage',
        'gpu': 'VRAM usage',
        'gpu_error': 'NVIDIA GPU not detected',
        'gpu_table': 'Processes on GPU',
        'other_machines': 'Other machines in network'
    },
    'pt': {
        'header': 'Monitor de Recursos do Sistema',
        'cpu': 'Uso da CPU',
        'ram': 'Uso da RAM',
        'disk': 'Uso de disco',
        'gpu': 'Uso de VRAM',
        'gpu_error': 'GPU NVIDIA não detectada',
        'gpu_table': 'Processos na GPU',
        'other_machines': 'Outras máquinas na rede'
    }
}


def parse_args():
    parser = ArgumentParser('Show system resources usage')
    parser.add_argument('--disks', nargs='+', help='Disks to show. Pairs of <mount_point> <name>', default=[])
    parser.add_argument('--interval', type=float, help='psutil\'s interval for capturing CPU usage', default=1.0)
    parser.add_argument('--bar_width', type=int, help='Width of progress bars', default=40)
    parser.add_argument('--lang', type=str, choices=['pt', 'en'], help='Language to output monitor info', default='pt')
    parser.add_argument('--hide_gpu_procs', action='store_true', help='Whether to show GPU procs or not', default=False)

    parser.add_argument('--netdata_resources', action='store_true', help='Whether to show netdata resources of other nodes in network', default=False)
    parser.add_argument('--netdata_host', type=str, help='Netdata host address to fetch node info', default=None)

    return parser.parse_args()
    

def get_cpu_usage(interval=1):
    return psutil.cpu_percent(interval=interval)


def get_ram_usage():
    vram = psutil.virtual_memory()
    return vram.used, vram.total, vram.percent


def get_disk_usage():
    disks = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disks.append({
                "device": partition.device,
                "mount": partition.mountpoint,
                "used": usage.used,
                "total": usage.total,
                "percent": usage.percent
            })
        except PermissionError:
            continue
    return disks


import xml.etree.ElementTree as ET


def get_nvidia_gpu_usage():
    try:
        result = subprocess.run(
            ["nvidia-smi", "-q", "-x"],
            capture_output=True,
            text=True,
            check=True
        )

        root = ET.fromstring(result.stdout)

        gpus = []

        for gpu in root.findall("gpu"):
            gpu_name = ' '.join(gpu.find("product_name").text.split()[-2:])
            util = float(gpu.find("utilization/gpu_util").text.replace(" %", ""))
            mem_used = float(gpu.find("fb_memory_usage/used").text.replace(" MiB", ""))
            mem_total = float(gpu.find("fb_memory_usage/total").text.replace(" MiB", ""))

            processes = []
            processes_node = gpu.find("processes")

            if processes_node is not None:
                for proc in processes_node.findall("process_info"):
                    pid = int(proc.find("pid").text)
                    name = proc.find("process_name").text
                    vram = float(
                        proc.find("used_memory").text.replace(" MiB", "")
                    )

                    # Get username safely
                    try:
                        username = psutil.Process(pid).username()
                    except (psutil.NoSuchProcess,
                            psutil.AccessDenied,
                            psutil.ZombieProcess):
                        username = "unknown"

                    processes.append({
                        "pid": pid,
                        "name": name,
                        "user": username,
                        "vram": vram
                    })

            # Sort processes by GPU memory usage descending
            processes.sort(key=lambda p: p["vram"], reverse=True)

            gpus.append({
                "name": gpu_name,
                "util": util,
                "mem_used": mem_used,
                "mem_total": mem_total,
                "processes": processes
            })

        return gpus

    except Exception:
        return []


def print_table(rows, width=None, color='', col_format={}, faint_rows=0):
    if not rows:
        print("(empty)")
        return

    # Collect all unique keys (preserve order)
    columns = []
    for row in rows:
        for key in row.keys():
            if key not in columns:
                columns.append(key)

    # Convert values to strings
    str_rows = []
    for row in rows:
        str_row = {}
        for col in columns:
            val = row.get(col)
            formatter = col_format.get(col)
            if formatter:
                val = formatter(val)
            
            str_row[col] = str(val)

        str_rows.append(str_row)

    # Base column widths (content-driven)
    widths = {}
    for col in columns:
        max_content = max(len(r[col]) for r in str_rows)
        widths[col] = max(len(col), max_content)

    # Compute minimal table width
    n = len(columns)
    min_width = sum(widths.values()) + n + 1

    # Stretch largest column if width is specified and larger than minimal
    if width:
        largest_col = max(widths, key=widths.get)
        extra = width - min_width
        widths[largest_col] += extra

    # Truncate content if needed
    def truncate(text, max_len):
        if len(text) <= max_len:
            return text
        return text[:max_len - 1] + "…"

    # Header
    header = " " + " ".join(
        truncate(col, widths[col]).ljust(widths[col])
        for col in columns
    ) + " "
    print(f'{color}{NEGATIVE}{header}{RESET}')

    # Rows
    for j,row in enumerate(str_rows):
        line = " " + " ".join(
            truncate(row[col], widths[col]).ljust(widths[col]) if i < len(columns)-1 else
            truncate(row[col], widths[col]).rjust(widths[col])
            for i,col in enumerate(columns)
        ) + " "
        if len(str_rows) - j <= faint_rows:
            print(f'{color}{FAINT}{line}{RESET}')
        else:
            print(f'{color}{line}{RESET}')


def main():
    args = parse_args()
    disks = {args.disks[i]: args.disks[i+1] for i in range(0, len(args.disks), 2)}
    interval = args.interval
    bar_width = args.bar_width
    strings = locale[args.lang]

    main_color = WHITE
    label_color = BLUE

    str = ''

    str += 'HEADER\n'
    
    # CPU
    cpu = get_cpu_usage(interval)
    str += f"{label_color}{strings['cpu']}{RESET} "
    str += progress_bar(cpu, width=bar_width) + '\n'

    # RAM
    used, total, _ = get_ram_usage()
    str += f"{label_color}{strings['ram']}{RESET} "
    str += progress_bar(used=used, total=total, width=bar_width) + '\n'

    # Disks
    for disk in get_disk_usage():
        mount = disk['mount']

        if disks and mount not in disks:
            continue
        
        disk_name = disks.get(mount, mount)
        str += f"{label_color}{strings['disk']} ({disk_name}){RESET} "
        used = disk['used']
        total = disk['total']
        str += progress_bar(used=used, total=total, width=bar_width) + '\n'

    # GPU
    gpus = get_nvidia_gpu_usage()
    processes = []
    if gpus:
        for i, gpu in enumerate(gpus):
            gpu_id = f'GPU{i} ' if len(gpus) > 1 else ''

            used = gpu['mem_used']*1024**2
            total = gpu['mem_total']*1024**2
            str += f"{label_color}{strings['gpu']} ({gpu_id}{gpu['name']}){RESET} "
            str += progress_bar(used=used, total=total, width=bar_width, color_percents=(40, 70)) + '\n'

            processes += gpu['processes']
    else:
        str += f"{RED}[{strings['gpu_error']}]{RESET}"


    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    largest_line_len = max([len(ansi_escape.sub('', line)) for line in str.splitlines()])
    for line in str.splitlines():
        clean_line = ansi_escape.sub('', line)
        diff = largest_line_len - len(clean_line)

        if line.startswith('HEADER'):
            print(f'{BOLD}{main_color}' + largest_line_len*'═')
            print(strings['header'].center(largest_line_len))
            print(largest_line_len*'═' + f'{RESET}')
            print()
        elif clean_line.startswith('['):
            print(clean_line.center(largest_line_len).replace(clean_line, line))
        else:
            line = diff*' ' + line
            print(line)

    if gpus and not args.hide_gpu_procs:
        total_gpu_mem_use = sum([p['vram'] for p in processes])
        faint_rows = sum([p['vram'] < total_gpu_mem_use*0.2 for p in processes])
        print(f'{main_color}{UNDERLINE}' + ' '*largest_line_len + f'{RESET}')
        print(f'{main_color}' + strings['gpu_table'].center(largest_line_len) + f'{RESET}')
        print_table(processes, width=largest_line_len, color=main_color, 
                    col_format={'vram': lambda x: format_bytes_compact(x*1024**2)}, faint_rows=faint_rows)
        
    print(largest_line_len*'═')

    if args.netdata_resources:
        from .netdata_resources import print_netdata_resources
        import socket

        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        print(strings['other_machines'].center(largest_line_len))
        print(largest_line_len*'═')

        print_netdata_resources(args.netdata_host, largest_line_len, skip_ip=local_ip)
    
        print(largest_line_len*'═')


if __name__ == "__main__":
    main()
