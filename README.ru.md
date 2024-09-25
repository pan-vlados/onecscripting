# onecscripting

Целью данного пакета является упрощение взаимодействия с базами данных 1С через COMobjects с использованием языка Python. Доступ к базе данных осуществляется по логину и паролю и зависит от прав вашего пользователя в этой базе данных.

> Пакет:
 - содержит приемы (методы), которые может использовать консультант по информационной безопасности, работающий с RBAC.
 - позволяет создавать сценарии/автоматизировать работу с базой данных 1С.
 - **работает только для ОС Windows**.

# Начальная конфигурация:

1. Установите клиент 1С версии 8.3 (**поддерживаемые версии >= 8.3.21.164**).
2. Зарегистрируйте dll для вашей конкретной -version- (из-за политики безопасности она может быть не установлена ​​по умолчанию на шаге 1, см. [это](https://its.1c.ru/db/edtdoc/content/10397/hdoc)):
```PowerShell
regsvr32 "C:\Program Files\1cv8\-version-\bin\comcntr.dll"
```
3. Настройте пользователя в базе данных 1С:
    - получите права доступа:
        - Внешнее подключение (StartExternalConnection);
        - *(необязательно)* чтение/запись/и т.д.;
    - установите аутентификацию по логину и паролю (домен/ОС не допускается, только 1С:Предприятие);
    - дополнительно для COM-подключения в панели управления (верхняя панель):
        - снимите флажок *Инструменты -> Настройки пользователя -> Запрашивать подтверждение при закрытии программы (Сервис->Настройки пользователя->Запросить подтверждение при закрытии программы)*;
        - выберите *Инструменты -> Настройки пользователя -> Запретить открытие нескольких сеансов (Сервис->Настройки пользователя->Запретить открытие нескольких сеансов)*.

## Использование

### Инициализация
```python
from onecscripting.infobase import OneC


user: str = 'user'
password: str = 'password'
host: str = 'host'
database: str = 'database'

onec = OneC()
```
Я предполагаю, что вы не знакомы с API 1С, поэтому перед подключением к базе данных вам следует вызвать `onec = OneC()`. Это позволяет вам работать с предопределенными методами класса `OneC`.

##### Синхронное соединение
```python
with onec.connect(host=host, database=database, user=user, password=password):
    # do some stuff
    pass
```
##### Асинхронное соединение
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
### Получить всех пользователей базы данных
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
### Изменение пароля по истечению срока
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

> Подробнее об использовании см. дополнительные примеры в [/tests dir](tests) и [примеры задач 1С](examples/onecguitasks.py).


## TODO:
1) Implement PEP 249;
2) Python standart async/await support;
3) Check for password change applied.


## LICENSE
> MIT