import os
from machine import UART

from datetime import datetime


def setup():
    '''
    Set up logging to REPL and UART0.
    '''
    uart = UART(0, 115200)
    os.dupterm(uart)  # send all print output to UART0 for logging


def log(*args, **kwargs):
    now = datetime.now().compact_fmt()
    print(f'{now}', *args, **kwargs)

