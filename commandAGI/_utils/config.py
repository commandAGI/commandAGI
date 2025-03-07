import os
from pathlib import Path

import platformdirs

PROJ_DIR = Path(__file__).parent.parent.parent
APPDIR = Path(platformdirs.user_data_dir(appname="commandAGI", appauthor="commandAGI"))

DEV_MODE = os.getenv("DEV_MODE", "false").lower().strip() == "true"
