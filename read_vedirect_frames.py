
import logging

import serial

from .vedirect import VictronVedirect

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    ve = VictronVedirect(port='COM7')
    ve.read(limit=5, callback=print)