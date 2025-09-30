from contextlib import contextmanager
from typing import Generator

import pymssql

from .config import get_settings


@contextmanager
def get_db_connection() -> Generator[pymssql.Connection, None, None]:
    settings = get_settings()
    connection = pymssql.connect(
        server=settings.db_server,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        login_timeout=5,
    )
    try:
        yield connection
    finally:
        connection.close()
