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
rm -rf resource_monitor.egg-info/`
```

## Arguments

Here are the arguments available when running the script:

* `--disks` - Disks to show. Provide pairs of `<mount_point> <name>` to define which disks should be displayed and the label to use for each one. Defaults to printing all mounting points

* `--interval` - `psutil` interval (in seconds) used to capture CPU usage. Defaults to `1.0`

* `--bar_width` - Width of progress bars in characters. Defaults to `40`

* `--lang` - Language used to output monitor information. Choices are `pt` and `en`. Default: `pt`

## Example output

Running the following:

```sh
python3 resource_monitor/main.py --disks / SSD --bar_width 50 --lang en
```

Prints something like the following on the terminal:

![Example result form ](example.png)