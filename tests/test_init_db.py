from core.db import (
    get_number_languages,
    get_number_roles,
    get_number_tables,
    get_number_test_types
)


def test_init_db():
    assert get_number_tables() == 8


def test_insert_data():
    assert get_number_languages() == 45
    assert get_number_test_types() == 6
    assert get_number_roles() == 3
