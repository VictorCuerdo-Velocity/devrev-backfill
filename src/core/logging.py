from typing import Optional
import logging

class ContextLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def info(self, msg: str, **kwargs):
        self.logger.info(f"{msg} {kwargs if kwargs else ''}")

    def error(self, msg: str, **kwargs):
        self.logger.error(f"{msg} {kwargs if kwargs else ''}")
