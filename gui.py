import sys

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
        self.css_provider = Gtk.CssProvider()
        self.logger = logger

        self.display_manager = display_manager
        self.displays = self.display_manager.displays
        self.assign_flag_strings()

        self.selected_displays = []
        self.selected_flags = [[] for _ in range(len(self.displays))]
        self.display_mode_objects = []
        self.flags_check_menu_items = []
        self.display_layouts = []
        self.status_labels = []
        self.initial_active_states = []

        self.turn_on_display = turn_on_display
        self.turn_off_display = turn_off_display

        self.window = Gtk.Window(title="Moni-Py")
        self.window.set_default_size(520, 200)

        self.window.connect("destroy", Gtk.main_quit)
        self.main_box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.set_margin_top(12)
        self.main_box.set_margin_bottom(12)
        self.window.add(self.main_box)

        # Create a Stack and a StackSwitcher
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(
                Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(200)
        self.stack.set_size_request(520, 160)

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(self.stack)

        self.main_box.pack_start(stack_switcher, False, False, 0)
        self.main_box.pack_start(self.stack, False, False, 1)

        self.submit_button = Gtk.Button(label="Submit")
        self.submit_button.connect("clicked", self.submit)

    def setup_menubar(self, display_info, i):
        display_status = display_info["status"]
        display_type = display_info["type"]

        box = Gtk.Box(spacing=0)
        box.set_homogeneous(False)
        box.set_size_request(520, 0)

        menubar_left = Gtk.MenuBar()
        menubar_right = Gtk.MenuBar()

        flags_menu = Gtk.Menu()
        flags_menuitem = Gtk.MenuItem(label='filter')
        flags_menuitem.set_submenu(flags_menu)

        check_menuitem = Gtk.CheckMenuItem.new_with_label(" status:")
        status_menuitem = Gtk.MenuItem.new_with_label("")

        if display_status == "active":
            initial_state = True
        else:
            initial_state = False
        check_menuitem.set_active(initial_state)
        self.initial_active_states.append(initial_state)

        flag_items = [
            (flag, description, Gtk.CheckMenuItem(label=description))
            for flag, description in self.FLAGS.items()
            ]
        for _, _, check_menu_item in flag_items:
            check_menu_item.connect(
                    "toggled", self.update_display_modes)
            flags_menu.append(check_menu_item)
        self.flags_check_menu_items.append(flag_items)

        if display_type == "extended":
            layout_menu = Gtk.Menu()
            layout_menuitem = Gtk.MenuItem(label="layout")
            layout_menuitem.set_submenu(layout_menu)

            layouts = ["clone", "left", "right", "above", "below"]
            group = None
            for layout in layouts:
                layout_radioitem = Gtk.RadioMenuItem \
                    .new_with_label_from_widget(group, layout)
                layout_radioitem.connect(
                    "toggled",
                    lambda radio_item=layout_radioitem,
                    i=i: self.layout_changed(layout_menuitem, radio_item, i)
                    )
                group = layout_radioitem
                layout_menu.append(layout_radioitem)
            menubar_right.append(layout_menuitem)

        menubar_left.append(check_menuitem)
        menubar_left.append(status_menuitem)

        menubar_right.append(Gtk.SeparatorMenuItem())
        menubar_right.append(flags_menuitem)

        box.pack_start(menubar_left, True, True, 0)
        box.pack_end(menubar_right, False, False, 0)

        return box, check_menuitem, status_menuitem

    def apply_css_to_widget(self, widget, color):
        css = f"""
        #status {{
            color: {color};
            font-style: oblique;
            opacity: 0.8;
        }}
        """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes(css.encode()))
        widget.set_name("status")
        Gtk.StyleContext.add_provider(
            widget.get_style_context(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def update_display_status(self, check_menuitem, status_menuitem, i):
        is_active = check_menuitem.get_active()
        color = "green" if is_active else "red"
        self.apply_css_to_widget(status_menuitem.get_child(), color)
        status_menuitem.set_label("active" if is_active else "inactive")
        self.toggle_modes(check_menuitem, i)
        status_menuitem.queue_draw()

    def create_display_box(self, display_info, i):
        display_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        display_grid = Gtk.Grid()
        display_box.pack_start(display_grid, False, False, 0)
        display_grid.set_size_request(400, 160)

        # Add the display box to the stack
        self.stack.add_titled(
                display_box, display_info["name"], display_info["name"]
                )

        menubar, check_menuitem, status_menuitem = self.setup_menubar(
                display_info, i)
        display_grid.attach(menubar, 0, 0, 1, 1)

        # Create a new container for the modes.
        mode_box = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, spacing=10)
        mode_box.set_halign(Gtk.Align.CENTER)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(
                Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        scrolled_window.set_size_request(400, 160)
        scrolled_window.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
        scrolled_window.add(mode_box)

        display_grid.attach(scrolled_window, 0, 1, 2, 1)
        return display_box, mode_box, check_menuitem, status_menuitem

    def create_mode_objects(self, modes, mode_box):
        mode_group = None
        display_modes_list = []
        for j, mode in enumerate(modes):
            refresh_rate = mode["dot_clock"] / (
                    mode["width"] * mode["height"])
            flag_string = self.get_flag_string(mode)
            formatted_mode = f"({mode['width']} x {mode['height']}" \
                             f" {round(refresh_rate)} Hz\n" \
                             f"Flags: {flag_string}"

            mode_radio_button = Gtk.RadioButton. \
                new_with_label_from_widget(mode_group, formatted_mode)
            mode_radio_button.set_sensitive(False)
            mode_group = mode_radio_button

            # Add each mode to the mode_box.
            mode_box.pack_start(mode_radio_button, False, False, 0)
            display_modes_list.append((mode, mode_radio_button))

        return display_modes_list

    def show(self):
        try:
            for i, display_info in enumerate(self.displays):
                display_box, mode_box, check_menuitem, status_menuitem = \
                    self.create_display_box(display_info, i)
                modes = sorted(
                        display_info["modes"],
                        key=lambda x: x['width'],
                        reverse=True
                        )
                display_modes_list = self.create_mode_objects(modes, mode_box)
                self.display_mode_objects.append(display_modes_list)

                self.selected_displays.append(
                        (display_info["name"],
                         (check_menuitem, status_menuitem),
                         display_modes_list, display_info["type"],
                         display_info["status"], display_info["crtc"],
                         None)
                        )
                check_menuitem.connect(
                    "toggled",
                    lambda check_menuitem=check_menuitem,
                    status_menuitem=status_menuitem, i=i:
                    self.update_display_status(
                        check_menuitem, status_menuitem, i)
                    )

            input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            input_box.set_halign(Gtk.Align.END)
            input_box.set_margin_top(10)
            input_box.set_margin_end(10)

            cancel_button = Gtk.Button(label="Cancel")
            cancel_button.connect("clicked", self.destroy_top_level_parent)

            input_box.pack_start(self.submit_button, False, False, 0)
            input_box.pack_start(cancel_button, False, False, 0)
            self.main_box.pack_start(input_box, False, False, 0)

            # Set check check_menuitems if display is active
            for i, display_info in enumerate(self.displays):
                check_menuitem = self.selected_displays[i][1][0]
                status_menuitem = self.selected_displays[i][1][1]
                self.update_display_status(check_menuitem, status_menuitem, i)
                if self.initial_active_states[i]:
                    self.toggle_modes(check_menuitem, i)

            self.window.show_all()
            self.update_display_modes(None)
            Gtk.main()
        except Exception as e:
            self.logger.exception(e)
            self.logger.debug(sys.exc_info())

    def filter_by_width(self, display_info):
        """
        Function to filter by width.
        If highest_first is True, sort by highest width first, else sort
        by smallest width first.
        """
        modes = display_info['modes']
        # Create a map from resolution to mode with highest dot_clock
        resolution_to_mode_map = {}
        for mode in modes:
            resolution = (mode['width'], mode['height'])
            if resolution not in resolution_to_mode_map or                \
                    mode['dot_clock'] > resolution_to_mode_map[
                            resolution]['dot_clock']:
                resolution_to_mode_map[resolution] = mode
        # Sort the modes by width
        sorted_modes = sorted(
            resolution_to_mode_map.values(),
            key=lambda x: x['width'],
            reverse=True
            )
        return sorted_modes

    def toggle_modes(self, widget, i):
        state = widget.get_active()
        display_info = self.selected_displays[i]
        display_name, status_elements, _, display_type, display_status,  \
            display_crtc, selected_mode = display_info

        for mode, mode_menu_item in self.display_mode_objects[i]:
            mode_menu_item.set_sensitive(state and all(
                (flag & mode['flags']) == flag
                for flag, _, check_menu_item
                in self.flags_check_menu_items[i]
                if check_menu_item.get_active()
                ))

        if not state:
            for _, mode_menu_item in self.display_mode_objects[i]:
                mode_menu_item.set_active(False)

        else:
            selected_mode = next(
                (mode for mode, mode_menu_item
                 in self.display_mode_objects[i]
                 if mode_menu_item.get_active()), None
                )

            if selected_mode:
                self.selected_displays[i] = (
                        display_name,  status_elements,
                        self.display_mode_objects[i], display_type,
                        display_status, display_crtc, selected_mode,
                        )
        self.window.queue_draw()

    def layout_changed(self, label, menuitem, i):
        if menuitem.get_active():
            text = menuitem.get_label()
            label.set_label(f"layout: {text}")
            self.display_layouts.append(text)
            menuitem.queue_draw()

    def update_display_modes(self, widget):
        for i, display_info in enumerate(self.displays):
            self.selected_flags = [
                    flag[0] for flag in self.flags_check_menu_items[i]
                    if flag[2].get_active()
                    ]
            sorted_modes = self.filter_by_width(display_info)
            for mode, mode_radio_button in self.display_mode_objects[i]:
                should_hide = mode not in sorted_modes or not all(
                    (mode['flags'] & flag) == flag
                    for flag in self.selected_flags
                    )
                should_show = mode in sorted_modes and all(
                    (mode['flags'] & flag) == flag
                    for flag in self.selected_flags
                    )
                mode_radio_button.set_visible(should_show and not should_hide)
        self.window.queue_draw()

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

    def get_flag_string(self, mode):
        flag_string = ""
        last_flag = mode["flag_strings"][-1]

        for flag in mode["flag_strings"][:-1]:
            flag_string += f"{flag}, "

        flag_string += last_flag
        return flag_string

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
            display_name, status_elements, display_modes, display_type,  \
                    display_status, display_crtc, selected_mode = display_info
            if status_elements[0].get_active():
                selected_displays.append(
                    (display_name, status_elements, display_modes,
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

        self.execute_display_operations(
                selected_displays, unselected_displays)

    def execute_display_operations(self, selected_displays,
                                   unselected_displays):
        if selected_displays:
            last_display = selected_displays[-1]
            for i, display in enumerate(selected_displays[:-1]):
                name, _, _, _, status, crtc, mode = display
                if status == "inactive":
                    self.turn_on_display_callback(
                            name,
                            mode,
                            crtc,
                            unselected_displays,
                            self.display_layouts[i],
                            callback=None
                            )
            self.turn_on_display_callback(
                    last_display[0],
                    last_display[6],
                    last_display[5],
                    unselected_displays,
                    self.display_layouts[-1],
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
                                 layout, callback=None):
        def callback_wrapper():
            self.turn_on_display(name, mode, crtc, layout)
            if callback:
                callback(unselected_displays)
        GLib.timeout_add_seconds(1, callback_wrapper)

    def turn_off_display_callback(self, name, crtc, callback=None):
        def callback_wrapper():
            self.turn_off_display(name, crtc)
            if callback:
                callback()
        GLib.timeout_add_seconds(1, callback_wrapper)
