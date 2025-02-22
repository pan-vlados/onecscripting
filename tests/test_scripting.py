import configparser
import logging
import unittest
from pathlib import Path

from src.onecscripting.infobase import OneC


TEST_CONFIG_FILENAME = 'test_config.ini'
logging.basicConfig(
    format='\n[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%d.%m.%Y %H:%M',
    level=logging.DEBUG,  # set to CRITICAL if you are not interested to see some results
)
logger = logging.getLogger(__name__)


class TestOneCDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config_dbtest = configparser.ConfigParser()
        cls.config_dbtest.read(Path(__file__).absolute().parent / TEST_CONFIG_FILENAME)
        cls.onec = OneC()
        cls._resource = cls.onec.connect(
            **dict(cls.config_dbtest.items('DBTEST')),
        )
        cls._resource.__enter__()

    # @unittest.skip('Skipped')
    def test_session_in_connection_info(self):
        for session in self.onec.sessions.values():
            if test_result := (
                session.login == self.config_dbtest.get('DBTEST', 'user')
                and session.connectiontype == 'COMConnection'
            ):
                logger.debug('%s' % session)
                break
        else:
            test_result = False
        self.assertTrue(test_result)

    # @unittest.skip('Skipped')
    def test_get_user_property(self):
        user = self.onec.current_user
        email = self.onec.to_string(user.COMObject.Email)
        authentification_standart = user.COMObject.StandardAuthentication
        authentification_os = user.COMObject.OSAuthentication
        os_username = user.COMObject.OSUser
        password_setting_date = user.COMObject.PasswordSettingDate
        password_is_set = user.COMObject.PasswordIsSet
        logger.debug(f'{email}')
        logger.debug(f'{authentification_standart}')
        logger.debug(f'{authentification_os}')
        logger.debug(f'{os_username}')
        logger.debug(f'{password_setting_date}')
        logger.debug(f'{password_is_set}')

    # @unittest.skip('Skipped')
    def test_check_password_is_expired(self):
        user = self.onec.current_user
        if not user.password_is_set:
            logger.debug('Password is not set.')
            return
        days_to_expire: int = 0
        if user.password_is_expire(
            days_to_expire=days_to_expire,
        ):
            logger.debug(f'Password expired. {user.password_setting_date=}, {days_to_expire=}.')

    # @unittest.skip('Skipped')
    def test_find_user_by_fullname(self):
        fullname = self.config_dbtest.get('TEST_VALUES', 'user_fullname1')
        user = self.onec.get_user_by_fullname(fullname)
        self.assertEqual(user.fullname, fullname)

    # @unittest.skip('Skipped')
    def test_get_users_roles_by_fullname(self):
        for i in range(1, 4):
            fullname = self.config_dbtest.get('TEST_VALUES', f'user_fullname{i}')
            user = self.onec.get_user_by_fullname(fullname)
            if not user:
                continue
            self.assertEqual(user.fullname, fullname)
            logging.debug(
                'User=%s:\n%s'
                % (
                    user.name,
                    '\n'.join(
                        f'Role Name={user_role.Name}, Synonym={user_role.Synonym}'
                        for user_role in user.roles
                    ),
                ),
            )

    # @unittest.skip('Skipped')
    def test_query_iteraitor1(self):
        query: str = """
            SELECT
                СправочникПольз.Наименование AS name,
                СправочникПольз.ПометкаУдаления AS deletemark,
                СправочникПольз.нн_ДатаПоследнегоВхода AS dates
            FROM
                Catalog.Пользователи AS СправочникПольз
            WHERE
                СправочникПольз.Наименование = &username
            """
        query = self.onec.execute_query(
            query,
            username=self.config_dbtest.get('TEST_VALUES', 'user_fullname1'),
        )
        try:
            while query.__next__():
                logger.debug(
                    f'\n {query.query.name} {query.query.dates} {query.query.deletemark}',
                )
        except StopIteration:
            pass

    # @unittest.skip('Skipped')
    def test_query_iteraitor2(self):
        query: str = """
        SELECT top 5
            ГруппыПользователейПользователиГруппы.Ссылка AS group_link,
            ГруппыПользователейПользователиГруппы.НомерСтроки AS number,
            ГруппыПользователейПользователиГруппы.Пользователь AS name
        FROM
            Catalog.ГруппыПользователей.ПользователиГруппы AS ГруппыПользователейПользователиГруппы
        """

        query = self.onec.execute_query(query)
        try:
            while query.__next__():
                logger.debug(
                    '№%s:\n%s %s'
                    % (
                        query.query.number,
                        self.onec.to_string(query.query.name),
                        self.onec.to_string(query.query.group_link),
                    ),
                )
        except StopIteration:
            pass

    # @unittest.skip('Skipped')
    def test_query_with_array_parameters(self):
        query: str = """
        SELECT
            Users.Наименование AS user,
            Users.ИдентификаторПользователяИБ AS user_id
        FROM
            Catalog.Пользователи AS Users
        WHERE
            Users.Наименование IN (&usernames)
            AND Users.ПометкаУдаления = False
        """
        usernames = [
            self.config_dbtest.get('TEST_VALUES', f'user_fullname{i}') for i in range(1, 3)
        ]
        usernames.append(self.config_dbtest.get('TEST_VALUES', 'user_deleted1'))
        query = self.onec.execute_query(
            query,
            usernames=usernames,
        )
        logger.debug('test_query_with_array_parameters:\n%s' % '\n'.join(row.user for row in query))

    @classmethod
    def tearDownClass(cls):
        if logger.level == logging.DEBUG:
            print()
        cls._resource.__exit__(None, None, None)


if __name__ == '__main__':
    unittest.main(verbosity=2)
