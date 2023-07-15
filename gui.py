import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


class GUI:
    FLAGS = {
        1: "HSyncPositive",
        2: "HSyncNegative",
        4: "VSyncPositive",
        8: "VSyncNegative",
        16: "Interlace",
        32: "DoubleScan",
        64: "CSync",
        128: "CSyncPositive",
        256: "CSyncNegative",
        }

    def __init__(self, display_manager, turn_on_display, turn_off_display,
                 logger):
        self.logger = logger

        self.display_manager = display_manager
        self.displays = self.display_manager.displays
        self.assign_flag_strings()

        self.selected_displays = []
        self.selected_flags = []
        self.display_mode_objects = []

        self.turn_on_display = turn_on_display
        self.turn_off_display = turn_off_display

        self.window = Gtk.Window(title="Moni-Py")
        self.window.set_default_size(600, 400)
        self.window.connect("destroy", Gtk.main_quit)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_margin_top(30)
        main_box.set_margin_bottom(60)
        main_box.set_margin_start(60)
        main_box.set_margin_end(0)
        self.window.add(main_box)

        title_box = Gtk.Box()
        title_box.set_halign(Gtk.Align.CENTER)
        title_box.set_center_widget()
        main_box.pack_start(title_box, False, False, 0)

        title = Gtk.Label()
        title.set_halign(Gtk.Align.CENTER)
        title.set_justify(Gtk.Justification.CENTER)
        title.set_markup(
                '''
                <span><b><big><big><big>Moni-Py</big></big></big></b>
                <i><big>Simple multihead screen managment.</big></i></span>
                '''
                )

        title_box.pack_start(title, False, False, 0)

        self.outer_grid = Gtk.Grid()
        self.outer_grid.set_halign(Gtk.Align.CENTER)
        self.outer_grid.set_column_spacing(10)
        self.outer_grid.set_row_spacing(10)
        main_box.pack_start(self.outer_grid, False, False, 0)

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
            row = 0
            column = 0

            for i, display_info in enumerate(self.displays):
                if i % 3 == 0 and i != 0:
                    row += 2
                    column = 0

                display_name = display_info["name"]
                modes = display_info["modes"]
                display_type = display_info["type"]
                display_status = display_info["status"]
                display_crtc = display_info["crtc"]
                selected_mode = None

                display_box = Gtk.Box(
                        orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                display_grid = Gtk.Grid()
                display_grid.set_column_spacing(10)
                display_grid.set_row_spacing(0)
                display_box.pack_start(display_grid, True, True, 0)
                display_grid.set_size_request(580, 190)
                self.outer_grid.attach(display_box, column, row, 1, 1)

                display_label = Gtk.Label()
                display_label.set_alignment(0, 0)
                display_label.set_justify(Gtk.Justification.LEFT)
                display_label.set_markup(
                        f'''
                        <b><big><big>
                        {display_name}
                        </big></big></b>
                        '''
                        )

                display_check_button = Gtk.CheckButton()
                display_check_button.set_size_request(25, 25)
                display_check_button.set_alignment(0, 0)
                display_check_button.connect("toggled", self.toggle_display, i)

                label_box = Gtk.Box(
                        orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
                display_grid.attach(label_box, 0, 0, 2, 1)
                label_box.pack_start(display_check_button, False, False, 0)
                label_box.pack_start(display_label, False, False, 1)

                # Create a new container for the modes.
                mode_box = Gtk.Box(
                        orientation=Gtk.Orientation.VERTICAL, spacing=10)

                scrolled_window = Gtk.ScrolledWindow()
                scrolled_window.set_policy(
                        Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
                scrolled_window.set_min_content_height(190)
                scrolled_window.set_min_content_width(280)
                scrolled_window.set_size_request(580, 190)
                scrolled_window.add(mode_box)

                display_grid.attach(scrolled_window, 0, 1, 2, 1)

                mode_group = None
                display_modes_list = []
                for j, mode in enumerate(modes):
                    refresh_rate = mode['dot_clock'] / (mode['width']
                                                        * mode['height'])
                    formatted_mode = f"({mode['width']} x {mode['height']}"   \
                                     f" {round(refresh_rate)} Hz"             \
                                     f" {mode['flag_strings']}"

                    mode_radio_button = Gtk.RadioButton.                      \
                        new_with_label_from_widget(
                                 mode_group, formatted_mode)
                    mode_radio_button.set_sensitive(False)
                    mode_group = mode_radio_button

                    # Add each mode to the mode_box.
                    mode_box.pack_start(mode_radio_button, False, False, 0)

                    display_modes_list.append((mode, mode_radio_button))
                self.display_mode_objects.append(display_modes_list)
                self.selected_displays.append(
                    (display_name, display_check_button,
                     display_modes_list, display_type, display_status,
                     display_crtc, selected_mode)
                    )

                column += 1

            flag_grid = Gtk.Grid()
            flag_grid.set_column_spacing(10)
            flag_grid.set_row_spacing(5)

            flag_keys = list(self.flags_check_buttons.keys())
            for i in range(1):
                for j in range(9):
                    if i * 9 + j >= len(flag_keys):
                        break
                    flag = flag_keys[i * 9 + j]
                    check_button = self.flags_check_buttons[flag]
                    flag_grid.attach(check_button, j, i, 1, 1)
            self.outer_grid.attach(flag_grid, 0, row + 1, 9, 1)

            input_box = Gtk.Box(
                    orientation=Gtk.Orientation.HORIZONTAL, spacing=40)

            submit_box = Gtk.Box(
                    orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            cancel_box = Gtk.Box(
                    orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

            cancel_button = Gtk.Button(label="Cancel")
            cancel_button.connect("clicked", self.destroy_top_level_parent)

            submit_box.pack_start(self.submit_button, True, True, 0)
            cancel_box.pack_start(cancel_button, True, True, 0)

            input_box.pack_start(submit_box, True, True, 0)
            input_box.pack_start(cancel_box, True, True, 0)

            self.outer_grid.attach(input_box, 0, row + 5, 2, 1)

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
        self.selected_flags = [
            flag for flag, check_button in self.flags_check_buttons.items()
            if check_button.get_active()
        ]
        for i, display_modes in enumerate(self.display_mode_objects):
            for mode, mode_radio_button in display_modes:
                flags = mode['flags']
                should_hide = not all(
                    (flags & flag) == flag for flag in self.selected_flags)
                if should_hide:
                    mode_radio_button.hide()
                else:
                    mode_radio_button.show()
            self.window.queue_draw()

    def toggle_display(self, widget, index):
        state = widget.get_active()
        display_info = self.selected_displays[index]
        display_name, display_check_button, _, display_type, display_status,  \
            display_crtc, selected_mode = display_info

        for mode, mode_radio_button in self.display_mode_objects[index]:
            mode_radio_button.set_sensitive(state and all(
                (flag & mode['flags']) == flag
                for flag, check_button in self.flags_check_buttons.items()
                if check_button.get_active()
            ))

        if not state:
            for _, mode_radio_button in self.display_mode_objects[index]:
                mode_radio_button.set_active(False)
        else:
            selected_mode = next(
                (mode for mode, mode_radio_button
                 in self.display_mode_objects[index]
                 if mode_radio_button.get_active()), None
            )
            if selected_mode:
                self.selected_displays[index] = (
                        display_name,  display_check_button,
                        self.display_mode_objects[index], display_type,
                        display_status, display_crtc, selected_mode,
                        )

    def get_flags(self, bitmask):
        flags = []
        for flag, description in self.FLAGS.items():
            if bitmask & flag:
                flags.append(description)
        return flags

    def assign_flag_strings(self):
        for display_info in self.displays:
            for mode in display_info['modes']:
                mode['flag_strings'] = self.find_flag_combinations(
                        mode['flags'])

    def find_flag_combinations(self, value):
        return [name for flag, name in self.FLAGS.items() if value & flag]

    def destroy_top_level_parent(self, widget):
        if widget.get_parent() is None:
            return

        parent = widget.get_parent()
        self.destroy_top_level_parent(parent)
        parent.destroy()

    def submit(self, button):
        selected_displays = []
        unselected_displays = []

        for display_info in self.selected_displays:
            display_name, display_check_button, display_modes, display_type,  \
                    display_status, display_crtc, selected_mode = display_info
            if display_check_button.get_active():
                selected_displays.append(
                    (display_name, display_check_button, display_modes,
                     display_type, display_status, display_crtc, selected_mode)
                )
            else:
                unselected_displays.append(
                        (display_name, display_crtc, display_status))

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

    def execute_display_operations(self, selected_displays,
                                   unselected_displays):
        if selected_displays:
            last_display = selected_displays[-1]
            for display in selected_displays[:-1]:
                name, _, _, _, status, crtc, mode = display
                if status == "inactive":
                    self.turn_on_display_callback(
                            name,
                            mode,
                            crtc,
                            unselected_displays,
                            callback=None
                            )
            self.turn_on_display_callback(
                    last_display[0],
                    last_display[6],
                    last_display[5],
                    unselected_displays,
                    callback=self.turn_on_displays_complete
                    )

    def turn_on_displays_complete(self, unselected_displays):
        if not unselected_displays:
            self.window.destroy()
            return

        last_display = unselected_displays[-1]
        for name, crtc, status in unselected_displays[:-1]:
            if status == "active":  # Check if the display is active
                self.turn_off_display_callback(name, crtc, callback=None)

        # set the callback to window destroy for the last display
        if last_display[1] == "active":  # Check if the display is active
            self.turn_off_display_callback(
                    name, crtc, callback=self.window.destroy)
        else:
            self.window.destroy()

    def turn_on_display_callback(self, name, mode, crtc, unselected_displays,
                                 callback=None):
        def callback_wrapper():
            self.turn_on_display(name, mode, crtc)
            if callback:
                callback(unselected_displays)
        GLib.timeout_add_seconds(1, callback_wrapper)

    def turn_off_display_callback(self, name, crtc, callback=None):
        def callback_wrapper():
            self.turn_off_display(name, crtc)
            if callback:
                callback()
        GLib.timeout_add_seconds(1, callback_wrapper)
