"""Structured logging utilities for APF."""
import logging
import json
import os
import sys
import time

def get_logger(component: str, run_id: str = None) -> logging.Logger:
    logger = logging.getLogger(component)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(h)
    def _emit(level: int, msg: str, **kw):
        rec = {"ts": time.time(), "component": component, "run_id": run_id, "msg": msg} | kw
        logger.log(level, json.dumps(rec, ensure_ascii=False))
    logger.json = _emit  # type: ignore[attr-defined]
    return logger
