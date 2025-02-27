import os
from pathlib import Path
import platformdirs

APPDIR = Path(platformdirs.user_data_dir(appname="commandLAB", appauthor="commandLAB"))
