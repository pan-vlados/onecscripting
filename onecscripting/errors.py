# -*- coding: utf-8 -*-
class UserIdentificationError(Exception):
    pass


class NotValidConnectionStringError(Exception):
    pass


class CannotChangePasswordError(Exception):
    pass


class PasswordIsNotChangedError(CannotChangePasswordError):
    pass