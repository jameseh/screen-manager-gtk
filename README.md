# Moni-Py

Moni-Py is a lightweight Python application that monitors for screens connected to your computer. When a new screen is connected, a GTK window pops up that allows you to select the state and mode of the screen.

## Requirements

* Python 3.6+
* python-xlib
* python-gobject

## Installation

```
git clone https://github.com/[your-username]/moni-py.git
cd moni-py
pip install -r requirements.txt
```

## Usage

```
python moni-py
```

This will start Moni-Py and it will begin monitoring for screens connected to your computer. When a new screen is connected, a GTK window will pop up that allows you to select the state and mode of the screen.

## State

The state of a screen can be either "on" or "off". In the Gtk GUI on is represented by a checked checkbox next the the display's name, off is unchecked.

## Mode

The mode of a screen is the resolution, refresh rate, and other attributes of the screen.

## License

Moni-Py is licensed under the MIT License.

## Contact

If you have any questions or feedback, please contact me at ii.jameseh@gmail.com 
