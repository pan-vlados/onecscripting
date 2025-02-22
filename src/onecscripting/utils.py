import functools
import logging
from typing import Any, Callable, TypeVar

import pythoncom


logger = logging.getLogger(__name__)


T = TypeVar('T')


def catch_com_error(func: Callable[..., T]) -> Callable[..., T]:
    """Catch and log all python com errors."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> ...:
        try:
            return func(*args, **kwargs)
        except pythoncom.com_error as ex:
            logger.exception('%s:' % type(ex).__name__)

    return wrapper
