import threading
import queue
import logging

from utils.logger import Logger
from display_manager import DisplayManager
from gui import GUI


class MoniPy:
    def __init__(self):
        self.event_queue = queue.Queue()
        self.logger = Logger()
        self.disp_mgr = DisplayManager(self.event_queue.put, self.logger)
        self.gui = GUI(
                self.disp_mgr,
                self.turn_on_display,
                self.turn_off_display,
                self.logger
                )

    def turn_on_display(self, name, mode, crtc):
        self.disp_mgr.turn_on_display(name, mode, crtc)

    def turn_off_display(self, name, crtc):
        self.disp_mgr.turn_off_display(name, crtc)

    def handle_event(self):
        while True:
            try:
                event = self.event_queue.get()
                if isinstance(event, str) and "display_added" in event:
                    self.gui.show()
                else:
                    logging.warning(f"Unexpected event: {event}")
            except Exception as e:
                logging.error(f"Error handling event: {e}")

    def run_display_monitor(self):
        self.disp_mgr.start_monitoring()

    def start(self):
        disp_mon_thread = threading.Thread(target=self.run_display_monitor)
        disp_mon_thread.start()

        event_handler_thread = threading.Thread(target=self.handle_event)
        event_handler_thread.start()


def main():
    moni_py = MoniPy()
    moni_py.start()


if __name__ == "__main__":
    main()
