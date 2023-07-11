import threading
import queue
import logging

from logger import Logger
from display_manager import DisplayManager
from gui import GUI


class MoniPy:
    def __init__(self):
        self.event_queue = queue.Queue()
        self.logger = Logger()
        self.disp_mgr = DisplayManager(self.event_queue.put, self.logger)
        self.gui = GUI(self.disp_mgr,
                       self.turn_on_display,
                       self.turn_off_display
                       )

    def turn_on_display(self, display_name, modes, display_type):
        self.disp_mgr.turn_on_display(display_name, modes, display_type)

    def turn_off_display(self, display_name):
        self.disp_mgr.turn_off_display(display_name)

    def handle_event(self):
        while True:
            try:
                event = self.event_queue.get()
                # Check if the event is a string and contains "display_added"
                if isinstance(event, str) and "display_added" in event:
                    self.gui.show()
                else:
                    logging.warning(f"Unexpected event: {event}")
            except Exception as e:
                logging.error(f"Error handling event: {e}")

    def run_display_monitor(self):
        self.disp_mgr.run_pre_monitor()
        self.disp_mgr.start_monitoring()

    def start(self):
        # Start the DisplayMonitor in a separate thread
        disp_mon_thread = threading.Thread(target=self.run_display_monitor)
        disp_mon_thread.start()

        # Start the event handler in a separate thread
        event_handler_thread = threading.Thread(target=self.handle_event)
        event_handler_thread.start()


def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    moni_py = MoniPy()
    moni_py.start()


if __name__ == "__main__":
    main()
