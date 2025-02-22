from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import win32com.client
from pywintypes import TimeType

from .errors import CannotChangePasswordError


class User:
    """Implementation of 1C SQL InfoBase user.

    Other COMObject properties which yo can call
    by address to COMObject.property:
            АдресЭлектроннойПочты (Email)
            АутентификацияOpenID (OpenIDAuthentication)
            АутентификацияOpenIDConnect (OpenIDConnectAuthentication)
            АутентификацияОС (OSAuthentication)
            АутентификацияСтандартная (StandardAuthentication)
            АутентификацияТокеномДоступа (AccessTokenAuthentication)
            ЗапрещеноВосстанавливатьПароль (CannotRecoveryPassword)
            ЗапрещеноИзменятьПароль (CannotChangePassword)
            ЗащитаОтОпасныхДействий (UnsafeOperationProtection)
            НастройкиВторогоФактораАутентификации (SecondAuthenticationFactorSettings)
            ОбработкаНастроекВторогоФактораАутентификации (SecondAuthenticationFactorSettingsProcessing)
            ОсновнойИнтерфейс (DefaultInterface)
            Пароль (Password)
            ДатаУстановкиПароля (PasswordSettingDate)
            ЗаписываемаяДатаУстановкиПароля (WritablePasswordSettingDate)
            ПарольУстановлен (PasswordIsSet)
            ПоказыватьВСпискеВыбора (ShowInList)
            ПользовательОС (OSUser) # AD login
            РазделениеДанных (DataSeparation)
            РежимЗапуска (RunMode)
            СохраняемоеЗначениеПароля (StoredPasswordValue)
            УникальныйИдентификатор (UUID)
            Язык (Language)
    """

    __slots__ = (
        'COMObject',
        'deletion_mark',
        'fullname',
        'name',
        'password_is_set',
        'password_setting_date',
        'roles',
    )

    def __init__(
        self, COMObject: win32com.client.CDispatch, deletion_mark: Optional[bool] = None
    ) -> None:
        self.name: str = COMObject.Name
        self.fullname: str = COMObject.FullName
        self.roles: List[win32com.client.CDispatch] = COMObject.Roles
        self.password_is_set: bool = COMObject.PasswordIsSet
        self.password_setting_date: TimeType = COMObject.PasswordSettingDate
        self.deletion_mark = deletion_mark
        self.COMObject: win32com.client.CDispatch = COMObject

    def __repr__(self) -> str:
        return f'User(name={self.name}, fullname={self.fullname})'

    def change_password(self, password: str) -> None:
        """Change password for User object in database by storing old
        password hash and comparing it with the new one. Function won't
        be completed if user to whom you perform operation have got
        OS/domain authentication.

        Warning:
            For security reasons it's strongly recommended don't hardcode your
            passwords. Use security methods such as Windows Data Protection
            API for storing and managing password in scripts.
            It's assumed that you submit an already decrypted password for
            this function.

        Note:
            Permission to change password can be manually turned off by
            selecting corresponding user's property in database.

        """
        if self.COMObject.CannotChangePassword:
            raise CannotChangePasswordError(
                '%s. Check permission to change password for User.' % self
            )
        # TODO: old_hash: str = self.COMObject.StoredPasswordValue
        self.COMObject.Password = password
        self.COMObject.Write()

        # TODO: implementation with old_hash checking.
        # We should close connection and open again for reading old_hash value.
        # Also we should try to test with no authorizations for changing password.
        # Now the problem is that we can paste same passsword as we've got in
        # database before.

        # TODO:  if old_hash == self.COMObject.StoredPasswordValue:
        # TODO:      raise PasswordIsNotChangedError('%s. Password hash didn\'t change.' % self)

    def password_is_expire(
        self,
        days_to_expire: int = 90,
        tz: timezone = timezone.utc,
    ) -> bool:
        """Check when user's password is expired.

        Parameters
        ----------
        - `days_to_expire` - number of days in which you expect the password to expire;
        - `tz` - databaze timezone, by default UTC+00.

        """
        # Convert to apropriate date format.
        last_password_change_date: datetime = datetime.strptime(
            str(self.password_setting_date),
            '%Y-%m-%d %H:%M:%S%z',
        )
        expire_delta: timedelta = timedelta(days=days_to_expire)
        # Calculate estimated password expiration date from last password change.
        estimated_expire_date: datetime = last_password_change_date + expire_delta
        # Find current date with timezone parameter (we always receive date
        # with timezone from database).
        current_date: datetime = datetime.now(tz=tz)
        return current_date > estimated_expire_date


def get_authorizations(users: List[User]) -> Dict[str, List[str]]:
    """Return user authorizations `{user.fullname: List[role.name]}`

    Warning:
        You can recive collisions due to the fact, that user.fullname
        is not unique object in InfoBase. It can give False-Positive
        results when user.fullname contain roles for other user with same
        user.fullname.
        To avoid this behavior use 'get_authorizations_unique' method,
        which allows you to work with pairs of tuples like
        (user.fullname, user.COMObject.OSUser) as an unique dictionary
        keys.

    """
    return {user.fullname: list(map(lambda x: x.name, user.roles)) for user in users}


def get_authorizations_unique(
    users: List[User],
) -> Dict[Tuple[str, str, Any, Optional[bool]], List[str]]:
    """Use OSuser value of User's objects to add uniqueness for user-role pairs.

    Return user authorizations `{
    (user.name, user.fullname, user.COMObject.OSUser, user.deletion_mark): List[role.name]
    }`
    """
    return {
        (user.name, user.fullname, user.COMObject.OSUser, user.deletion_mark): list(
            map(lambda x: x.name, user.roles)
        )
        for user in users
    }
