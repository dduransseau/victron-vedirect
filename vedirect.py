
import logging

import serial

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

from consts import LABEL_DEFINITIONS

class VictronVedirect:

    BAUD_RATE = 19200
    LABEL_DEFINITIONS = LABEL_DEFINITIONS

    def __init__(self, port='/dev/ttyAMA0'):
        self.port = port
        self._buffer = b""
        self._frame = b""
        self.buffer_size = 42 # 9 + 33 bytes as suggested in implementation guidelines
        self._parsed_frames = 0
        self._error_frames = 0
        self._state = dict()
        self._temp_block = dict()
        self._frame_callback = None
        self._line_callback = None

    @staticmethod
    def validate_checksum(frame):
        calculated_checksum = sum(frame) % 256
        return True if calculated_checksum == 0 else False

    def parse_frame(self):
        if self.validate_checksum(self._frame):
            logger.debug(f"Received valid frame: {self._frame}")
            self._frame = self._frame[:-10].strip() # Avoid to pass the checksum line since byte might be non chr
            frame_str = self._frame.decode()
            split_lines = frame_str.split("\r\n")
            logger.debug(f"Split frame: {split_lines}")
            for line in split_lines:
                # logger.debug(f"Line:{line}")
                self.parse_line(line)
            if self._frame_callback:
                self._frame_callback(self.display_state)
            return self.raw_state
        else:
            self._error_frames += 1

    def parse_line(self, line):
        try:
            label, value = line.split("\t")
            # logger.debug(f"Label: {label} value: {value}")
            self._state[label] = value
            if self._line_callback:
                self._line_callback((label, value))
        except ValueError:
            pass

    @property
    def parsed_frames(self):
        return self._parsed_frames

    def receive_data(self, data):
        self._buffer += data
        if b'\r\nChecksum' in self._buffer:
            end_frame_index = self._buffer.find(b"Checksum")
            if end_frame_index > 10:
                self._parsed_frames += 1
                end_frame_index += 10  # Add tab and checksum char to index
                self._frame = self._buffer[:end_frame_index]
                # print(complete_frame)
                self.parse_frame()
                # print("Complete frame", complete_frame)
                # print("Checksum result:", validate_checksum(complete_frame))
                self._buffer = self._buffer[end_frame_index:]

    @property
    def raw_state(self):
        return self._state

    @property
    def display_state(self):
        formatted_state = dict()
        for label, value in self._state.items():
            definition = self.LABEL_DEFINITIONS[label]
            if value_mapping := definition.get("value_mapping"):
                value = value_mapping[value]
            if value_unit := definition.get("unit"):
                value = f"{value}{value_unit}"
            formatted_state[definition["description"]] = value
        return formatted_state

    def _stop_condition(self, limit):
        if limit < 1:
            return True
        else:
            return self.parsed_frames < limit

    def read(self, limit=0, callback=None, line_callback=None, frame_callback=None):
        self._frame_callback = frame_callback or callback
        self._line_callback = line_callback
        try:
            connection = serial.Serial(port=self.port, baudrate=self.BAUD_RATE)
            while self._stop_condition(limit):
                data = connection.read(42)
                self.receive_data(data)
            connection.close()
        except KeyboardInterrupt:
            connection.close()

if __name__ == "__main__":
    ve = VictronVedirect(port='COM7')
    ve.read(limit=5, callback=print)