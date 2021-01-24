import os


BASE_DIR = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
DB_DIR = os.path.join(BASE_DIR, 'db')
INIT_DATA_DIR = os.path.join(BASE_DIR, 'init_data')


TOKEN = os.getenv('BOT_TOKEN')
BOT_NAME = os.getenv('BOT_NAME')


ADMINS = {
    ...,
}


COMMANDS = {
    'start_commands': {
        'start',
        'reset',
    },
    'user_commands': {
        'begin_test',
    },
    'test_creator_commands': {
        'add_questions',
        'delete_questions',
        'update_questions',
    },
    'information_commands': {
        'languages_list',
        'test_types_list',
    },
    'admin_commands': {
        'create_deep_link',
    },
}
