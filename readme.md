# System Resource Monitor

A simple resource monitor that shows the current CPU, RAM, drive and GPU usages, along with current GPU processes. This is useful to use on a machine learning lab infrastructure: run it when a user logs in via SSH and they'll have info on the machine's resources.

## Installing and running

### Via uv

To use the [uv](https://docs.astral.sh/uv/) package manager, init uv:

```
uv init
```

And add the package:
```
uv add "resource_monitor @ git+https://github.com/joao-luz/resource-monitor.git"
```

To run, do:

```
uv run resource_monitor
```

### Via pip

Create a virtual environment:

```
python -m venv .venv
```

Use the env's pip:

```
.venv/bin/pip install "resource_monitor @ git+https://github.com/joao-luz/resource-monitor.git"
```

To run, do:

```
.venv/bin/resource_monitor
```

### Via pipx

You may also use [pipx](https://github.com/pypa/pipx) to install it globally:

```
pipx install "resource_monitor @ git+https://github.com/joao-luz/resource-monitor.git"
```

To run, do:

```
resource_monitor
```

### Installing globally without pipx

If you want to have a globally callable `resource_monitor` script but can't do it via pipx, perform the following (you might need sudo privileges):

`cd` into a directory such as `/opt`, create a venv and install the package via the venv's pip:

```
python3 -m venv .venv
.venv/bin/pip install "resource_monitor @ git+https://github.com/joao-luz/resource-monitor.git"
```

Create a symbolic link from the package inside the venv to an executable placed in a dir like `/usr/local/bin`:

```
ln -s /opt/resource-monitor/.venv/bin/resource_monitor /usr/local/bin/resource_monitor
```

To run, do:

```
resource_monitor
```

## Netdata integration

[Netdata Cloud](www.netdata.cloud) is a tool for hardware monitoring machines in a network. We provide functionality to fetch data from a Netdata host in order to get information on the resource use of other nodes in the network, as well as expose theirs local IPs. This is useful in a lab setting as one might choose to log into other servers if the one thei're trying to access is currently in use.


## Arguments

Here are the arguments available when running the script:

* `--disks` - Disks to show. Provide pairs of `<mount_point> <name>` to define which disks should be displayed and the label to use for each one. Defaults to printing all mounting points

* `--interval` - `psutil` interval (in seconds) used to capture CPU usage. Defaults to `1.0`

* `--bar_width` - Width of progress bars in characters. Defaults to `40`

* `--lang` - Language used to output monitor information. Choices are `pt` and `en`. Defaults to `pt`

* `--hide_gpu_procs` - Whether to show GPU procs or not. Defaults to `False`

* `--netdata_host` - A host (including port) to fetch Netdata resource use across the network. Defaults to `None`

## Example output

Running the following:

```
resource_monitor --disks / SSD --bar_width 50 --lang en
```

Prints something like the following on the terminal:

![Example result form ](example.png)