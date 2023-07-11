from itertools import chain, combinations

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


class GUI:
    FLAGS = {
        1: "Supported by the monitor",
        2: "Preferred by the monitor",
        4: "Current mode",
        5: "Progressive scan mode",
        6: "Stereoscopic mode",
        8: "High-definition mode",
        16: "Ultra-high-definition mode",
        21: "Doubled refresh rate mode",
        32: "Low latency mode",
        37: "Double-wide mode",
        38: "Low latency mode and current mode",
        41: "Gamma-corrected mode",
        42: "Double-high mode",
        512: "Color-managed mode",
    }

    def __init__(self, display_manager, turn_on_display, turn_off_display,
                 logger=None):
        self.logger = logger

        self.display_manager = display_manager
        self.displays = self.display_manager.displays
        self.selected_displays = []
        self.turn_on_display = turn_on_display
        self.turn_off_display = turn_off_display

        self.window = Gtk.Window(title="display-manager-gtk")
        self.window.set_default_size(300, 200)
        self.window.set_border_width(20)
        self.window.connect("destroy", Gtk.main_quit)

        self.main_box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.main_box.set_margin_top(20)
        self.main_box.set_margin_bottom(20)
        self.main_box.set_margin_start(20)
        self.main_box.set_margin_end(20)
        self.window.add(self.main_box)

        self.label = Gtk.Label(label="Select the monitors to turn on/off:")
        self.main_box.pack_start(self.label, False, False, 0)

        self.outer_grid = Gtk.Grid()
        self.outer_grid.set_column_spacing(20)
        self.outer_grid.set_row_spacing(20)
        self.main_box.pack_start(self.outer_grid, False, False, 0)

        self.flags_check_buttons = {
            flag: Gtk.CheckButton(label=description)
            for flag, description in self.FLAGS.items()
        }
        for check_button in self.flags_check_buttons.values():
            check_button.connect("toggled", self.update_display_modes)

        self.submit_button = Gtk.Button(label="Submit")
        self.submit_button.connect("clicked", self.submit)

    def show(self):
        try:
            self.assign_flag_strings()
            row = 0
            column = 0

            for i, display_info in enumerate(self.displays):
                if i % 3 == 0 and i != 0:
                    row += 2
                    column = 0

                display_name = display_info['name']
                modes = display_info['modes']
                display_type = display_info['type']
                display_status = display_info['status']

                display_grid = Gtk.Grid()
                display_grid.set_column_spacing(10)
                display_grid.set_row_spacing(10)

                display_box = Gtk.Box(
                        orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                display_box.pack_start(display_grid, True, True, 0)
                self.outer_grid.attach(display_box, column, row, 1, 1)

                display_check_button = Gtk.CheckButton(label=display_name)
                display_check_button.connect("toggled", self.toggle_display, i)
                display_grid.attach(display_check_button, 0, 0, 2, 1)

                mode_grid = Gtk.Grid()
                mode_grid.set_column_spacing(10)
                mode_grid.set_row_spacing(10)

                scrolled_window = Gtk.ScrolledWindow()
                scrolled_window.set_policy(
                        Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
                scrolled_window.add(mode_grid)
                scrolled_window.set_min_content_height(190)
                scrolled_window.set_min_content_width(750)

                display_grid.attach(scrolled_window, 0, 1, 2, 1)

                display_modes = []
                mode_group = None

                for j, mode in enumerate(modes):
                    refresh_rate = mode['dot_clock'] / (mode['width']
                                                        * mode['height'])
                    formatted_mode = f"({mode['width']} x {mode['height']}" \
                                     f" {round(refresh_rate)} Hz" \
                                     f" {mode['flag_strings']}"

                    mode_radio_button = Gtk.RadioButton\
                        .new_with_label_from_widget(
                                mode_group, formatted_mode)
                    mode_radio_button.set_sensitive(False)
                    mode_grid.attach(mode_radio_button, j % 2, j // 2, 1, 1)
                    display_modes.append((mode, mode_radio_button))
                    mode_group = mode_radio_button

                self.selected_displays.append(
                    (display_name, display_check_button, display_modes,
                     display_type, display_status)
                )

                column += 1


            # WORKING ON BOTTOM CHECKBOX LAYOUT NEED IN OWN GRID
            display_grid = Gtk.Grid()
            display_grid.set_column_spacing(10)
            display_grid.set_row_spacing(10)

            # Reformatting flags into 3 columns and 5 rows
            flag_keys = list(self.flags_check_buttons.keys())
            for i in range(5):
                for j in range(3):
                    if i * 3 + j >= len(flag_keys):
                        break
                    flag = flag_keys[i * 3 + j]
                    check_button = self.flags_check_buttons[flag]
                    self.outer_grid.attach(check_button, j, row + i + 1, 1, 1)
            self.outer_grid.attach(self.submit_button, 0, row + 7, 3, 1)
            self.window.show_all()

            # Set display check button active if display is active
            for i, display_info in enumerate(self.displays):
                display_check_button = self.selected_displays[i][1]
                if display_info["status"] == "active":
                    display_check_button.set_active(True)
                    self.toggle_display(display_check_button, i)

            # Run the GTK main event loop
            Gtk.main()
        except Exception as e:
            self.logger.error(f"Error showing GUI: {e}")
            raise

    def update_display_modes(self, widget):
        for display_info in self.selected_displays:
            display_name, display_check_button, display_modes, display_type, \
                    display_status = display_info
            for mode, mode_radio_button in display_modes:
                # Check if the mode should be hidden.
                should_hide = not all(
                    self.FLAGS[flag] in mode['flag_strings']
                    for flag, check_button in self.flags_check_buttons.items()
                    if check_button.get_active()
                )

                # Hide the mode if it should be hidden.
                if should_hide:
                    mode_radio_button.hide()
                else:
                    mode_radio_button.show()

        self.window.queue_draw()  # Redraw the window to reflect the changes

    def toggle_display(self, widget, index):
        state = widget.get_active()
        display_info = self.selected_displays[index]
        display_name, display_check_button, display_modes, display_type, \
            display_status = display_info

        for mode, mode_radio_button in display_modes:
            mode_radio_button.set_sensitive(state and all(
                (flag & mode['flags']) == flag
                for flag, check_button in self.flags_check_buttons.items()
                if check_button.get_active()
            ))

        if not state:
            for _, mode_radio_button in display_modes:
                mode_radio_button.set_active(False)
        else:
            selected_mode = next(
                (mode for mode, mode_radio_button in display_modes
                 if mode_radio_button.get_active()), None
            )
            if selected_mode:
                self.selected_displays[index] = (
                        display_name, selected_mode, display_modes,
                        display_type, display_status
                        )

    def assign_flag_strings(self):
        for display_info in self.displays:
            for mode in display_info['modes']:
                mode['flag_strings'] = self.find_flag_combinations(
                        mode['flags'])[0]

    def find_flag_combinations(self, value):
        flags = list(self.FLAGS.keys())
        possible_combinations = []
        self._subset_sum(flags, len(flags)-1, value, [], possible_combinations)
        return possible_combinations[0]  # return the first/only combination

    def _subset_sum(self, flags, end, total, partial, possible_combinations):
        s = sum(partial)

        # check if the partial sum is equals to target
        if s == total:
            possible_combinations.append([self.FLAGS[i] for i in partial])
            return  # if we reach the number, stop further processing

        for i in range(end, -1, -1):
            n = flags[i]
            self._subset_sum(
                    flags, i-1, total, partial+[n], possible_combinations)

    def submit(self, button):
        selected_displays = []
        unselected_displays = []
        for display_info in self.selected_displays:
            display_name, display_check_button, display_modes, display_type, \
                    display_status = display_info
            if display_check_button.get_active():
                selected_displays.append(
                        (display_name, display_check_button, display_modes,
                         display_type)
                        )
            else:
                unselected_displays.append((display_name))

        if not selected_displays:
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Please select at least one display."
            )
            dialog.run()
            dialog.destroy()
            return

        self.execute_display_operations(selected_displays, unselected_displays)

    def execute_display_operations(
            self, selected_displays, unselected_displays):
        for display in selected_displays:
            display_name, display_check_button, display_modes, \
                    display_type = display
            self.turn_on_display_callback(
                display_name,
                display_modes,
                display_type,
                unselected_displays,
                callback=self.turn_on_displays_complete
            )

        for display_name in unselected_displays:
            self.turn_off_display_callback(
                    display_name, callback=self.window.destroy)

    def turn_on_displays_complete(self, unselected_displays):
        last_display = unselected_displays[-1]
        for display in unselected_displays[:-1]:
            self.turn_off_display_callback(display[0], callback=None)
        if last_display:
            self.turn_off_display_callback(
                last_display,
                callback=self.window.destroy
                )

    def turn_on_display_callback(
            self, display_name, display_modes, display_type,
            unselected_displays, callback=None):
        def callback_wrapper():
            self.turn_on_display(display_name, display_modes)
            if callback:
                callback(unselected_displays)
        GLib.timeout_add_seconds(1, callback_wrapper)

    def turn_off_display_callback(self, display_name, callback=None):
        def callback_wrapper():
            self.turn_off_display(display_name)
            if callback:
                callback()
        GLib.timeout_add_seconds(1, callback_wrapper)
