# System Resource Monitor

A simple resource monitor that shows the current CPU, RAM, drive and GPU usages, along with current GPU processes. This is useful to use on a machine learning lab infrastructure: run it when a user logs in via SSH and they'll have info on the machine's resources.

## Running

Install required packages:

```sh
pip install psutil
```

Then run:

```sh
python3 resource_monitor/main.py
```

## Installing as pipx package

[pipx](https://github.com/pypa/pipx) is a package manager for python applications. Use this tool to install `resource_monitor` as a package in your system. For that, `cd` into this repo's root directory and run:

```bash
pipx install .
```

For installing it globally, run:

```bash
pipx install --global .
```

You may remove the `build/` and `.egg-info/` dirs post installation:

```bash
rm -rf build/
rm -rf resource_monitor.egg-info/
```

## Installing without pipx

If you want to have a globally callable `resource_monitor` script but can't do it via pipx (e.g. you are using Ubuntu 24.04 and the available pipx version doesn't support the `--global` argument), you may either find another way to install a more recent version of pipx or perform the following workaroud (you'll need sudo privileges):

`cd` into a directory such as `/opt` and clone this repository:

```bash
git clone https://github.com/joao-luz/resource-monitor
cd resource-monitor
```

Create a venv and install the package via the venv's pip:

```bash
python3 -m venv .venv
source .venv/bin/activate
.venv/bin/pip install .
```

Create a symbolic link from the package inside the venv to an executable placed in a dir like `/usr/local/bin`:

```bash
ln -s /opt/resource-monitor/.venv/bin/resource_monitor /usr/local/bin/resource_monitor
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

```sh
python3 resource_monitor/main.py --disks / SSD --bar_width 50 --lang en
```

Prints something like the following on the terminal:

![Example result form ](example.png)