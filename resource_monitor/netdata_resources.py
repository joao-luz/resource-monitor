import requests
import sys
import json
import re

from .utils import progress_bar
from .ascii_escape import *


NETDATA_PORT = 19999

def pad_center(text, length, fill):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_text = ansi_escape.sub('', text)

    if len(clean_text) >= length:
        return text

    total_padding = length - len(clean_text)
    left_padding = total_padding // 2
    right_padding = total_padding - left_padding

    return f"{fill * left_padding}{text}{fill * right_padding}"


def print_usage_grid(nodes, width=60, spacing=2):
    col_width = (width - spacing) // 2

    def format_column(node):
        header_tag = f' {BOLD}{node["hostname"]}{RESET} ({node["ip"]}) '
        header = pad_center(header_tag, col_width, '═')

        gpu_tag = f'GPU ({node['gpu_name']})'
        ram_tag = (len(gpu_tag) - 3) * ' ' + 'RAM'

        bar_width = col_width - len(ram_tag) - 1
        ram_line = (
            f"{BLUE}{ram_tag}{RESET} "
            + progress_bar(used=node["ram_usage"], total=node["ram_total"], width=bar_width)
        )

        if node.get("gpu_total") and node["gpu_total"] > 0:
            bar_width = col_width - (len(gpu_tag) + 1)
            gpu_line = (
                f"{BLUE}{gpu_tag}{RESET} "
                + progress_bar(used=node["gpu_usage"], total=node["gpu_total"], width=bar_width)
            )
        else:
            gpu_line = f"{BLUE}GPU{RESET} (não disponível)"

        return [
            header.ljust(col_width),
            ram_line.ljust(col_width),
            gpu_line.ljust(col_width),
        ]

    for i in range(0, len(nodes), 2):
        left = format_column(nodes[i])
        right = format_column(nodes[i+1]) if i+1 < len(nodes) else [""]*3

        for l, r in zip(left, right):
            print(l + (' '*spacing) + r)

        print()


def get_nodes(host_address):
    try:
        r = requests.get(f'{host_address}/api/v3/nodes')
        r.raise_for_status()
        return r.json().get('nodes', [])
    except Exception as e:
        print('Failed to retrieve nodes:', e)
        sys.exit(1)


def get_all_metrics(ip):
    try:
        r = requests.get(f"http://{ip}:{NETDATA_PORT}/api/v3/allmetrics?format=json")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Failed to retrieve nodes:", e)
        sys.exit(1)

def get_ram_usage(all_metrics):
    key = 'system.ram'
    data = all_metrics[key]

    used = data['dimensions']['used']['value']
    free = data['dimensions']['free']['value']
    cached = data['dimensions']['cached']['value']
    buffers = data['dimensions']['buffers']['value']
    total = used + free + cached + buffers

    return used, total


def get_gpu_usage(all_metrics):
    key = [key for key in all_metrics.keys() if key.startswith('nvidia_smi') and key.endswith('frame_buffer_memory_usage')]
    if len(key) == 0:
        return None
    
    key = key[0]
    data = all_metrics[key]

    used = data['dimensions']['used']['value']
    free = data['dimensions']['free']['value']
    reserved = data['dimensions']['reserved']['value']
    total = used + free + reserved

    return used, total


def get_gpu_name(ip):
    # Getting the GPU name is a hastle, apparently this is what must be done:
    payload = {
        "scope": {"contexts": ["nvidia_smi.gpu_temperature"]},
        "selectors": {
            "nodes": ["*"],
            "contexts": ["*"],
            "instances": ["*"],
            "dimensions": ["*"],
            "labels": ["*"],
            "alerts": ["*"]
        },
        "window": {
            "after": -600,
            "before": 0,
            "points": 1
        },
        "aggregations": {
            "metrics": [{"group_by": ["selected"], "aggregation": "sum"}],
            "time": {"time_group": "average"}
        },
        "format": "json2",
        "options": ["jsonwrap", "minify", "unaligned"],
        "timeout": 1000
    }

    url = f"http://{ip}:{NETDATA_PORT}/api/v3/data"
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    data = response.json()

    labels = data.get("summary", {}).get("labels", [])
    for label in labels:
        if label.get("id") == "product_name":
            for value in label.get("vl", []):
                return value['id']
            
    return ''


def load_name_map(filepath, time_window='1_week'):
    import os
    import time

    if not os.path.exists(filepath):
        return {}
    
    parts = time_window.split('_')
        
    amount = float(parts[0])
    unit = parts[1].lower().replace('s', '')

    seconds_in_day = 24 * 60 * 60
        
    if unit == "day":
        seconds_limit = amount * seconds_in_day
    elif unit == "week":
        seconds_limit = amount * 7 * seconds_in_day
    elif unit == "month":
        seconds_limit = amount * 30 * seconds_in_day
    
    current_time = time.time()
    
    try:
        file_mtime = os.path.getmtime(filepath)
        
        if (current_time - file_mtime) < seconds_limit:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
                
    except (OSError, json.JSONDecodeError):
        return {}

    return {}


def print_netdata_resources(host_address, width=60, spacing=2, skip_ip=None):
    nodes = get_nodes(host_address)

    if not nodes:
        return

    # Getting the GPU name takes a long time via a /data query to netdata
    # so we'll use a simple local cache for gpu names and update it every week
    gpu_name_map_filepath = 'gpu_name_map.json'
    gpu_name_map = load_name_map(gpu_name_map_filepath)

    node_info = []

    for node in nodes:
        state = node.get('state')

        if state == 'stale':
            continue

        node_id = node.get("nd")
        hostname = node.get("nm", node_id)
        ip = node.get('labels').get('_net_default_iface_ip')

        if skip_ip and ip in skip_ip:
            continue

        all_metrics = get_all_metrics(ip)
        ram = get_ram_usage(all_metrics)
        gpu = get_gpu_usage(all_metrics)

        if gpu is None:
            continue
        
        if ip in gpu_name_map:
            gpu_name = gpu_name_map[ip]
        else:
            gpu_name = ' '.join(get_gpu_name(ip).split()[-2:])
            gpu_name_map[ip] = gpu_name
        
        node_info.append({
            'hostname': hostname,
            'ip': ip,
            'ram_usage': ram[0],
            'ram_total': ram[1],
            'gpu_usage': gpu[0],
            'gpu_total': gpu[1],
            'gpu_name': gpu_name
        })

    if width % 2:
        spacing += 1

    print_usage_grid(node_info, width=width, spacing=spacing)

    with open(gpu_name_map_filepath, 'w') as f:
        json.dump(gpu_name_map, f)