#!/usr/bin/env python
import sys

from Xlib import X
from Xlib.display import Display
from Xlib.ext import randr


class DisplayManager:
    """A class to monitor and set xorg display configurations."""

    def __init__(self, event_handler, logger):
        self.event_handler = event_handler
        self.logger = logger

        try:
            self.display = Display()
            self.root_window = self.display.screen().root
            self.root_window.change_attributes(
                    event_mask=(X.StructureNotifyMask))

            self.check_for_extensions()
            self.displays = self.get_connected_displays()
            if any(display["status"] == "inactive" for display
                   in self.displays):
                self.event_handler("initial_display_added")

        except Exception as e:
            self.logger.error(f"Error initializing DisplayManager: {e}")
            raise

    def start_monitoring(self):
        while True:
            event = self.display.next_event()
            if event:
                self.logger.info(f"EVENT: {event}")
                self.process_event(event)

    def set_event_handler(self, event_handler):
        self.event_handler = event_handler

    def process_event(self, event):
        if event.type == X.ConfigureNotify:
            self.update_display_info()
            if self.all_displays_inactive():
                primary_display = self.get_primary_display()
                if primary_display:
                    self.turn_on_display(
                        primary_display['name'],
                        primary_display['modes'],
                        primary_display['crtc']
                    )
                else:
                    self.logger.error("No primary display found.")
            elif self.new_display_added():
                self.event_handler("display_added")

    def get_connected_displays(self):
        resources = self.root_window.xrandr_get_screen_resources()
        primary_output = resources.crtcs[0]
        displays = []

        for output in resources.outputs:
            output_info = self.get_output_info(output)
            if output_info.connection == randr.Connected:
                display_info = self.get_display_info(
                        output_info, primary_output, resources)
                displays.append(display_info)

        return displays

    def check_for_extensions(self):
        try:
            randr_extension = self.display.query_extension('RANDR')
            if not randr_extension.present:
                self.logger.error('Server does not have the RANDR extension')
                sys.exit(1)

            r = self.display.xrandr_query_version()
            self.logger.info(
                    'RANDR version %d.%d' % (r.major_version, r.minor_version))
        except Exception as e:
            self.logger.error(f"Error checking for extensions: {e}")
            raise

    def get_position_based_on_primary(self, position):
        primary_display = self.get_primary_display()
        if not primary_display:
            self.logger.error("No primary display found.")
            return None

        if position == "right":
            return primary_display['modes'][0].width, 0
        elif position == "left":
            return -primary_display['modes'][0].width, 0
        elif position == "up":
            return 0, -primary_display['modes'][0].height
        elif position == "down":
            return 0, primary_display['modes'][0].height

    def turn_on_display(self, name, mode, crtc, position=None):
        resources = self.root_window.xrandr_get_screen_resources()
        crtc_list = [display["crtc"] for display in self.displays]
        matching_output = []
        x, y = 0, 0
        crtc = crtc
        if position:
            pos = self.get_position_based_on_primary(position)
            if pos is not None:
                x, y = pos

        for output in resources.outputs:
            output_info = self.get_output_info(output)
            if output_info.connection == randr.Connected                      \
                    and name == output_info.name:
                matching_output.append(output)
                for resource in resources.crtcs:
                    if resource not in crtc_list:
                        crtc = resource

        randr.set_crtc_config(
            self.display,
            crtc,
            X.CurrentTime,
            x=x,
            y=y,
            mode=mode.id,
            rotation=randr.Rotate_0,
            outputs=matching_output
            )

    def turn_off_display(self, name, crtc):
        resources = self.root_window.xrandr_get_screen_resources()
        matching_output = []
        x, y = 0, 0
        for output in resources.outputs:
            output_info = self.get_output_info(output)
            if output_info.connection == randr.Connected                      \
                    and name == output_info.name:
                matching_output.append(output)

        randr.set_crtc_config(
            self.display,
            crtc,
            X.CurrentTime,
            x=x,
            y=y,
            mode=0,
            rotation=randr.Rotate_0,
            outputs=matching_output
            )

    def get_output_info(self, output):
        return randr.get_output_info(
            self.display, output, X.CurrentTime)

    def get_display_info(self, output_info, primary_output, resources):
        display_name = output_info.name
        display_type = "primary" if output_info == primary_output             \
            else "extended"
        display_status = "active" if output_info.crtc != 0                    \
            else "inactive"

        modes = self.get_modes(output_info, resources)

        return {
            "name": display_name,
            "modes": modes,
            "type": display_type,
            "status": display_status,
            "crtc": output_info.crtc,
        }

    def get_modes(self, output_info, resources):
        modes = []
        for mode in resources.modes:
            if mode.id in output_info.modes:
                modes.append(mode)
        return modes

    def update_display_info(self):
        self.prev_connected_displays = self.displays
        self.displays = self.get_connected_displays()

    def get_primary_display(self):
        return next(
            (display for display in self.displays
             if display['type'] == "primary"), None)

    def all_displays_inactive(self):
        return all(
                display["status"] == "inactive" for display in self.displays)

    def new_display_added(self):
        return len(self.prev_connected_displays) < len(self.displays)


if __name__ == "__main__":
    display_manager = DisplayManager()
    display_manager.start_monitoring()
