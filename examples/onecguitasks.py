# -*- coding: utf-8 -*-
import logging
import win32com.client

from typing import Optional, List, Dict, Union, Tuple, Set

from onecscripting.dbobj import User, get_authorizations_unique


logger = logging.getLogger(__name__)


def check_users_assigments(
        connection: win32com.client.CDispatch,
        users: List[Optional[str]],
        new_users: bool,
        host: str,
        database: str,
        return_message: Optional[str] = None,
        retrospective_mode: bool = False,
        assignments_only_mode: bool = False
        ) -> Union[Optional[Dict[Tuple[str, ...], List[str]]], Optional[str]]:
    """
    Check the presence of users and roles in the 1C infobase
    via External connection (COMConnecter).

    Return user autoruzations (fullname and roles name).

    IMPORTANT! In asignments_only_mode=True keep silence and doesn't send return
    messages despite of result, cause we don't need to care about it.
    """

    if retrospective_mode:
        infobase_users: List[Optional[User]] = connection.get_all_users()
    else:
        infobase_users: List[Optional[User]] = connection.get_active_users_by_fullname(users)
        if not infobase_users:  # no users in DB
            if assignments_only_mode:
                return {(user, ''): 'WARNING: User not found' for user in users}, None
            if new_users:
                return None, None
            return_message = 'All users not found in in 1C Srvr=%s, Ref=%s.' % (host, database)
            message: str = '%s List:\n%s' % (return_message, '\n'.join(user for user in users))
            logger.warning(message)
            return None, return_message
        if new_users and not assignments_only_mode:
            return_message: str = 'Users already exists in 1C Srvr=%s, Ref=%s.' % (host, database)
            message: str = '%s List:\n%s' % (return_message, '\n'.join(user.fullname for user in infobase_users))
            logger.warning(message)
            return None, return_message

    users_authorizations: Dict[Tuple[str, ...], List[str]] = get_authorizations_unique(
        users=infobase_users
        )

    if not any(users_authorizations.values()):  # no user's roles in DB
        # there is possibility that user haven't got any roles
        # that's why we are checking that users_authorizations
        # contain any value
        if assignments_only_mode:
            return {(user, ''): 'WARNING: User haven\'t got any roles' for user in users}, None
        return_message: str = 'Users haven\'t got any roles in 1C Srvr=%s, Ref=%s.' % (host, database)
        message: str = '%s List:\n%s' % (return_message, '\n'.join(user.fullname for user, _ in infobase_users))
        logger.warning(message)
        return None, return_message

    if not retrospective_mode:
        users_differense: Set[Optional[str]] = set(users) - set(user for user, _ in users_authorizations.keys())
        if users_differense:  # some users missing in DB
            if assignments_only_mode:
                for user in users_differense:
                    users_authorizations[(user, '')] = 'WARNING: User not found'
            else:
                return_message = 'Users not found in in 1C Srvr=%s, Ref=%s.' % (host, database)
                message: str = '%s List:\n%s' % (return_message, '\n'.join(user for user in users_differense))
                logger.warning(message)
    return users_authorizations, return_message