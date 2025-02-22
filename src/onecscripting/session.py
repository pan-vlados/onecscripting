from dataclasses import dataclass


@dataclass(frozen=True)
class Session:
    """Implementation of 1C SQL session object."""

    login: str
    fullname: str
    connectiontype: str
    PCname: str
    IP: str
    time: str
    sessioninfo: str
    sessionnumber: str
