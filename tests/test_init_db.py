from core.db import get_number_tables
from core.init_db import _init_db


def test_init_db():
    _init_db()
    assert get_number_tables() == 8
