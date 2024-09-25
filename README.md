# onecscripting

Purpose of this package is to simplify interaction with 1C databases through COMobjects using Python language. Access to database carried out by login and password and depends on your user's rights in that database.

> The package:
 - contain techniques (methods) that can be used by an information security consultant working with RBAC.
 - allow you to make scripting/automation task to deal with 1C database.
 - **work only for Windows OS**.

## Initial configuration:

1. Install 1C client version 8.3 (**supported versions >= 8.3.21.164**).
2. Register dll for you sepcific -version- (due to security policy might not be installed by default in step 1, see [this](https://its.1c.ru/db/edtdoc/content/10397/hdoc)):
```PowerShell
regsvr32 "C:\Program Files\1cv8\-version-\bin\comcntr.dll"
```
3. Setup your user in 1C database:
    - grant access rights to:
        - External Connection (StartExternalConnection);
        - *(optional)* read/write/e.t.c;
    - set authentification by login and password (domain/OS not allowed, only 1C: Enterprise);
    - additional for COM connection in control panel (top bar):
        - deselect *Tools -> User Settings -> Request confirmation when closing the program (Сервис->Настройки пользователя->Запрашивать подтверждение при закрытии программы)*;
        - select *Tools -> User Settings -> Prevent opening multiple sessions (Cервис->Настройки пользователя->Запретить открытие нескольких сеансов)*.

## Usage

### Initialization
```python
from onecscripting.infobase import OneC


user: str = 'user'
password: str = 'password'
host: str = 'host'
database: str = 'database'

onec = OneC()
```
I'm assume that you aren't familiar with 1C API, that's why you should call `onec = OneC()` before connection to database. It's allow you to work with predefined class methods.

##### Sync conenction
```python
with onec.connect(host=host, database=database, user=user, password=password):
    # do some stuff
    pass
```
##### Async connection
```python
from typing import Dict, Any

from concurrent.futures import ThreadPoolExecutor, Future, as_completed


workers: int = 2  # number of threads
databases: Dict[str, str] = {
    'database1': 'host1',
    'database2': 'host2'
    }  # define databases parameters (let user and password be the same)

def job(system: OneC, **settings):
    with system.connect(**settings):
        # do some stuff in specific connection
        pass

# start async jobs
with ThreadPoolExecutor(max_workers=workers) as executor:
    jobs: Dict[Future, str] = {
        executor.submit(
            job,
            system=onec,
            host=host,
            database=database,
            user=user,
            password=password
            ): database for database, host in databases.items()
        }
    for future in as_completed(jobs):
        database: str = jobs[future]
        try:
            # get results of async jobs
            job_result: Any = future.result()
        except Exception as e:
            print('%s, %s' % (database, e))
        else:
            # do some stuff with job's result
            pass
```
### Get all database users
```python
from typing import List, Optional

from onecscripting.infobase import OneC
from onecscripting.dbobj import User


onec = OneC()
with onec.connect(
    host='host',
    database='database',
    user='user',
    password='password'
    ) as connection:
    infobase_users: List[Optional[User]] = connection.get_all_users()
```
### Change password if it's expired
```python
from onecscripting.infobase import OneC
from onecscripting.dbobj import User


onec = OneC()
with onec.connect(
    host='host',
    database='database',
    user='user',
    password='password'
    ) as connection:
    current_user: User = onec.current_user
    if current_user.password_is_expire(days_to_expire=30):
        current_user.change_password(password='new password')
```

> For more information about usage please see additional examples in [/tests dir](tests) and [1C examples tasks](examples/onecguitasks.py).


## TODO:
1) Implement PEP 249;
2) Python standart async/await support;
3) Check for password change applied.


## LICENSE
> MIT