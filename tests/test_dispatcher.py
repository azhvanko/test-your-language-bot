import pytest


@pytest.mark.parametrize(
    'text, result',
    (
        ('/start', True),
        ('/begin_test', True),
        ('start', False),
        ('12345', False),
        ('qwerty/start', False),
    )
)
def test_is_bot_command(dispatcher, text, result):
    assert dispatcher._is_bot_command(text) == result


@pytest.mark.parametrize(
    'command, result',
    (
        ('/start', ('start', None)),
        ('/begin_test', ('begin_test', None)),
        ('/start 2aefdcc2-5c09-4e29-bdea', ('start', None)),
        ('/start 2aefdcc2_5c09_4e29_bdea_ee61fdc01f23', ('start', None)),
        (
            '/start 2aefdcc2-5c09-4e29-bdea-ee61fdc01f23',
            ('start', '2aefdcc2-5c09-4e29-bdea-ee61fdc01f23')
        ),
    )
)
def test_get_bot_command(dispatcher, command, result):
    assert dispatcher._get_bot_command(command) == result
