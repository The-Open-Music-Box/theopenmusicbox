import re

class LogFilter:
    IGNORED_PATTERNS = [
        "pygame.*Hello from the pygame community.*",
        "Restarting with stat",
        "Debugger is active!",
        "Debugger PIN:.*",
        "wsgi starting up on.*"
    ]

    @classmethod
    def should_log(cls, message: str) -> bool:
        return not any(re.match(pattern, message) for pattern in cls.IGNORED_PATTERNS)

    @classmethod
    def clean_message(cls, message: str) -> str:
        message = re.sub(r'\[blue\]', '', str(message))
        message = re.sub(r'\[/.*?\]', '', message)
        message = re.sub(r'✓\s*✓', '✓', message)
        return message.strip()
