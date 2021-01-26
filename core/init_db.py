import os.path

from .config import INIT_DATA_DIR
from .db import execute_script


def _init_db(script_path: str = INIT_DATA_DIR) -> None:
    """Initializes db."""
    _script_path = os.path.join(script_path, 'create_db.sql')
    with open(_script_path, mode='r') as file:
        script = file.read()
    execute_script(script)
