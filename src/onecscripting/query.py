from __future__ import annotations
from typing import Dict, List, Optional, Union

import win32com.client


class Query:
    """Implementation of 1C SQL query."""

    def __init__(
        self,
        connection: win32com.client.CDispatch,
        statement: str,
        **parameters: Optional[Dict[str, Union[str, List[str]]]],
    ) -> None:
        self._connection: win32com.client.CDispatch = connection
        self.query: win32com.client.CDispatch = self._connection.NewObject(
            'Query',
            statement,
        )
        if parameters:
            self.set_parameters(**parameters)

    def set_parameters(self, **parameters: Optional[Dict[str, Union[str, List[str]]]]) -> None:
        """Parameters can be used in the query statement, which must
        be explicitly passed to the query statement using the
        SetParameter() method of the query object. This method allow
        to set value in position marked by & symbol.
        """
        for parameter, value in parameters.items():
            if isinstance(value, list):
                # We create arrays when list of elements provided.
                array = self._connection.NewObject('Array')
                for element in value:
                    array.Add(element)
                self.query.SetParameter(parameter, array)
                continue
            self.query.SetParameter(parameter, value)

    def execute(self) -> None:
        self.query = self.query.Execute()

    @property
    def empty(self) -> bool:
        """Check if query result is empty after execution of query object.

        Can be accessed only after query.execute() method, otherwise
        will raise AttributeError: <unknown>.IsEmpty.
        """
        return self.query.IsEmpty()

    def unload(self) -> List[win32com.client.CDispatch]:
        """Not optimized way to work with query result, cause store all
        data in memory.
        Return a list (named table in 1C) of query object's values.
        You can go through list by simple python loop:
        ```python
            for value in query:
                value.property
                ...
        ```
        """
        return self.query.Unload()

    def choose(self) -> QueryIterator:
        """Prefferd way by 1C to get and work with query result,
        cause get data from the database in fixed size chunks.

        Return query object (iterator) which you can go trought
        by method:
        ```python
            for value in query:
                value.property
                ...
        ```
        """
        return QueryIterator(self.query.Choose())

    def result(self, unload: bool = False) -> Union[List[win32com.client.CDispatch], QueryIterator]:
        """Return query result. If there is no result in query,
        return None.
        """
        self.execute()
        # if self.empty:
        #     return []
        if unload:
            return self.unload()
        return self.choose()


class QueryIterator:
    """Implementation of 1C query.Choose() iterator which
    change standart iteration behavior from <while> loop
    to <for> loop.

    Return row values in query. Each iteration you access
    new row value.

    Before:
    ```python
        while query.Next():
            query.property
            ...
    ```
    Now:
    ```python
        for value in query:
            value.property
            ...
    ```
    """

    def __init__(self, query: win32com.client.CDispatch) -> None:
        self.query = query

    def __iter__(self) -> QueryIterator:
        return self

    def __next__(self) -> win32com.client.CDispatch:
        if self.query.Next():
            return self.query
        raise StopIteration
