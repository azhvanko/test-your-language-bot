from core.db import (
    get_admin_ids,
    get_number_languages,
    get_number_questions,
    get_number_roles,
    get_number_tables,
    get_number_test_types
)
from core.init_db import _get_files_list


def test_admin_ids():
    assert len(get_admin_ids()) > 0


def test_get_files_list():
    files = _get_files_list()
    assert files == ['language_test_1.txt', 'language_test_2.txt']


def test_init_db():
    assert get_number_tables() == 8


def test_insert_data():
    assert get_number_languages() == 45
    assert get_number_test_types() == 6
    assert get_number_roles() == 3
    assert get_number_questions() > 0
