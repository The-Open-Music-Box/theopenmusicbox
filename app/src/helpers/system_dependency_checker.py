# app/src/helpers/system_dependency_checker.py

import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)

@dataclass
class DependencyError:
    name: str
    message: str

class SystemDependencyChecker:
    @staticmethod
    def check_ffmpeg() -> Optional[DependencyError]:
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            return DependencyError(
                name="ffmpeg",
                message="FFmpeg binary not found in PATH"
            )

        try:
            subprocess.run(['ffmpeg', '-version'],
                         capture_output=True,
                         text=True,
                         check=True)
            return None
        except Exception as e:
            return DependencyError(
                name="ffmpeg",
                message=f"Error executing FFmpeg: {str(e)}"
            )

    @staticmethod
    def check_dependencies() -> List[DependencyError]:
        errors = []
        ffmpeg_error = SystemDependencyChecker.check_ffmpeg()
        if ffmpeg_error:
            errors.append(ffmpeg_error)
        return errors