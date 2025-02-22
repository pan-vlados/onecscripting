import logging
import re
from contextlib import contextmanager
from string import Template
from typing import Dict, Iterator, List, Optional, Union

import pythoncom
import win32com.client

from .dbobj import User
from .query import Query, QueryIterator
from .session import Session


logger = logging.getLogger(__name__)


class OneC:
    """Implementation of 1C class for external COM connection to the InfoBase."""

    # TODO: rewrite in PEP249 https://peps.python.org/pep-0249/. Use https://github.com/thesketh/pep249
    # TODO: add errors resolver and some suggestions:
    # errors = {
    #     'Неверные или отсутствующие параметры соединения с информационной базой': UserIdentificationError,
    #     'Идентификация пользователя не выполнена\nНеправильное имя или пароль пользователя': NotValidConnectionStringError
    #     } # execinfo [2]
    connection_string: Template = Template(
        'Srvr="$host";Ref="$database";Usr="$user";Pwd="$password";',
    )

    connection: win32com.client.CDispatch

    @contextmanager
    def connect(
        self,
        host: str,
        database: str,
        user: str,
        password: str,
    ) -> Iterator[win32com.client.CDispatch]:
        """Initialize external COM connection to 1C database version 8.3*.

        Due to extensive (resource-dependent) connection we are using context
        manager for the reason to realease resources. If we will not realease
        resources and set connection=None, we will recive daemon session in 1C,
        which you can't close.

        Way to connect without context manager:
        ```python
            onec = OneC()
            connection = onec.connect(host, database, user, password)
            connection.__enter__()
            # do some stuff
            connection.__exit__(None, None, None)
        ```
        """
        # Initializes the COM library for use by the calling thread, sets the
        # thread's concurrency model, and creates a new apartment for the thread
        # if one is required. Without this you can't perform async operation with
        # database connection.
        pythoncom.CoInitialize()

        logger.info('Attempting to connect 1C Srvr=%s, Ref=%s.' % (host, database))
        try:
            self.connection = win32com.client.Dispatch('V83.COMConnector').Connect(
                self.connection_string.substitute(
                    host=host,
                    database=database,
                    user=user,
                    password=password,
                ),
            )
            logger.info('Connection established.')
            yield self.connection
        # except pythoncom.com_error as ex: # TODO: catch different exception
        #     logger.exception('%s:' % type(ex).__name__)
        except Exception as ex:
            logger.exception('Srvr=%s, Ref=%s. %s:' % (host, database, type(ex).__name__))
            raise
        else:
            logger.info('Operation completed.')
        finally:
            self.close_connection()
            pythoncom.CoUninitialize()
            logger.info('Connection closed.')

    def execute_query(
        self,
        statement: str,
        unload: bool = False,
        **parameters: Optional[Dict[str, Union[str, List[str]]]],
    ) -> Optional[Union[List[win32com.client.CDispatch], QueryIterator]]:
        """Execute 1C SQL query with specified data parameters
        by symbol & in statement.

        Warning:
            unloud=True load all query data into the memory and
            return list of query object's values. Do not unload
            the query result to an intermediate table unless it
            necessary.

        For parameters wich represented by arrays you should use
        "IN (&parameter)" in statement instead of "= &parameter".

        Example:
            1) ГруппыПользователейПользователиГруппы.Пользователь = &Пользователь
            2) ГруппыПользователейПользователиГруппы.Пользователь IN (&МассивПользователей)

        Default use:
        ```python
            for value in query:
                value.property
                ...
        ```

        """
        return Query(
            self.connection,
            statement=statement,
            **parameters,
        ).result(unload=unload)

    def to_string(self, COMObject: win32com.client.CDispatch) -> str:
        """Convert 1C COMObject to string representation."""
        return self.connection.String(COMObject)

    @property
    def sessions(
        self,
        split_pattern: str = '; | \(|, |\)',
    ) -> Dict[int, Session]:
        """Get information about working sessions in InfoBase
        delimited by `split_pattern`.
        """
        return {
            i: Session(
                *re.split(split_pattern, self.connection.String(session))[:8],
            )
            for i, session in enumerate(self.connection.GetInfoBaseSessions())
        }

    @property
    def current_user(self) -> User:
        """Get current connection's InfoBase user."""
        return User(self.connection.InfoBaseUsers.CurrentUser())

    def get_user_by_name(self, name: str) -> Optional[User]:
        """Return user by login credentials in InfoBase if user exists.

        Example:
        ```python
            name='1C_Jhon D.'
        ```

        """
        user = self.connection.InfoBaseUsers.FindByName(name)
        if not user:
            return None
        return User(user)

    def get_user_by_fullname(self, fullname: str) -> Optional[User]:
        """Return user by combination of first, second and (if applicable)
        middle name if user exists.

        Example:
            fullname='Jhon Duglas'

        """
        for user in self.connection.InfoBaseUsers.GetUsers():
            if user.FullName == fullname:
                return User(user)
        return None

    def get_all_users(
        self,
        with_deletion_mark: bool = False,
        unload: bool = False,
    ) -> List[User]:
        """Get all InfoBase users."""
        if with_deletion_mark:
            statement: str = """
            SELECT
                Users.ИдентификаторПользователяИБ AS uuid,
                Users.DeletionMark AS deletion_mark
            FROM
                Catalog.Пользователи AS Users
            WHERE
                Users.ИдентификаторПользователяИБ IS NOT NULL
            """
            query = Query(self.connection, statement=statement, parameters=None).result(
                unload=unload
            )
            return [
                User(COMObject, user.deletion_mark)
                for user in query
                if hasattr(COMObject := self.connection.InfoBaseUsers.FindByUUID(user.uuid), 'Name')
            ]  # TODO: without hasattr AttributeError for COMObject: 'NoneType' object has no attribute 'Name'
        return [User(user) for user in self.connection.InfoBaseUsers.GetUsers()]

    def get_active_users_by_fullname(
        self, full_names: List[str], with_deletion_mark: bool = False, unload: bool = False
    ) -> List[User]:
        """Checking for the existing of users in the 1C users catalog
        by full_names. If deletion mark for user is set to True, this
        user will be shown as well.

        Return list of users which exists in 1C users catalog.
        """
        statement: str = """
        SELECT
            Users.ИдентификаторПользователяИБ AS uuid,
            Users.DeletionMark AS deletion_mark
        FROM
            Catalog.Пользователи AS Users
        WHERE
            Users.Description IN (&full_names)
        """
        if not with_deletion_mark:
            statement += ' AND NOT Users.DeletionMark'
        query = Query(
            self.connection, statement=statement, parameters={'full_names': full_names}
        ).result(unload=unload)
        return [
            User(self.connection.InfoBaseUsers.FindByUUID(user.uuid), user.deletion_mark)
            for user in query
        ]

    def close_connection(self) -> None:
        """Close COM connection to database.

        Setting <Request confirmation when closing the program> must be
        deselected in user's setting of the corresponding InfoBase.
        """
        self.connection = None  # type: ignore
