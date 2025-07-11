"""Logging helpers to only log on main process."""

import functools
import logging
import os

from axolotl.utils.distributed import is_main_process

# Adapted from Accelerate
# https://github.com/huggingface/accelerate/blob/main/src/accelerate/logging.py


class MultiProcessAdapter(logging.LoggerAdapter):
    """
    Logger adapter for distributed logging, specifically to only log on main process.
    """

    @staticmethod
    def _should_log(main_process_only: bool):
        return not main_process_only or is_main_process()

    def log(self, level, msg, *args, **kwargs):
        main_process_only = kwargs.pop("main_process_only", True)
        kwargs.setdefault("stacklevel", 2)

        if self.isEnabledFor(level) and self._should_log(main_process_only):
            msg, kwargs = self.process(msg, kwargs)
            self.logger.log(level, msg, *args, **kwargs)

    @functools.lru_cache(maxsize=10)
    def warning_once(self, *args, **kwargs):
        """
        This method is identical to `logger.warning()`, but will emit the warning with the same message only once

        Note: The cache is for the function arguments, so 2 different callers using the same arguments will hit the
        cache. The assumption here is that all warning messages are unique across the code. If they aren't then need to
        switch to another type of cache that includes the caller frame information in the hashing function.
        """
        self.warning(*args, **kwargs)


def get_logger(name: str, log_level: str | None = None) -> MultiProcessAdapter:
    if log_level is None:
        log_level = os.environ.get("AXOLOTL_LOG_LEVEL", None)
    logger = logging.getLogger(name)
    if log_level is not None:
        logger.setLevel(log_level.upper())
        logger.root.setLevel(log_level.upper())
    return MultiProcessAdapter(logger, extra={})
