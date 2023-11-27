# -*- coding: utf-8 -*-
import logging
import pythoncom
import functools

from typing import Callable, TypeVar, Any


logger = logging.getLogger(__name__)


T = TypeVar('T')


def catch_com_error(func: Callable[..., T]) -> Callable[..., T]:
    """Catch and log all python com errors."""
    @functools.wraps
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except pythoncom.com_error as ex:
            logger.exception('%s:' % type(ex).__name__)
    return wrapper
