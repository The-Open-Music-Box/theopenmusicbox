# app/run.py

import sys
import traceback
from pathlib import Path

from src.server import create_server, run_server
from src.config import Config
from src.monitoring.improved_logger import ImprovedLogger, LogLevel
from src.helpers.exceptions import AppError

project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

logger = ImprovedLogger(__name__)


def main():
    try:
        logger.log(LogLevel.INFO, "Loading configuration")
        config = Config()

        logger.log(LogLevel.INFO, "Creating server instance")
        app, socketio = create_server(config)
        run_server(app=app, socketio=socketio, config=config)
        return 0

    except AppError as e:
        logger.log(LogLevel.ERROR, f"Application error: {str(e)}")
        return 1

    except Exception as e:
        logger.log(LogLevel.ERROR, f"Unexpected error: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())