# Screen-Manager-GTK

![Python 3.6+](https://img.shields.io/badge/python-3.6%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Screen-Manager-GTK is a lightweight Python application that monitors for screens connected to your computer. When a new screen is connected, a GTK window pops up that allows you to select the state and mode of the screen.

![screen-manager-gtk screenshot](/screenshots/screen-manager-gtk-00.png)

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [State](#state)
- [Mode](#mode)
- [License](#license)
- [Contact](#contact)

## Requirements

- Python 3.6+
- python-xlib
- python-gobject

## Installation

```bash
git clone https://github.com/jameseh/screen-manager-gtk.git
cd screen-manager-gtk
pip install -r requirements.txt
```

## Usage

```bash
python screen-manager-gtk.py
```

This will start Screen-Manager-GTK and it will begin monitoring for screens connected to your computer. When a new screen is connected, a GTK window will pop up that allows you to select the state and mode of the screen.

## State

The state of a screen can be either "on" or "off". In the GTK GUI, "on" is represented by the status being active or inactive. Screens can be toggled active or inactive with a checkbutton.

## Mode

The mode of a screen refers to the resolution, refresh rate, and other attributes.

## License

Screen-Manager-GTK is licensed under the [MIT License](LICENSE).

## Contact

If you have any questions or feedback, please contact me at ii.jameseh@gmail.com
