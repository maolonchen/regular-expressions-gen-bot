import os
import sys
import logging
import threading
from typing import Optional
from pathlib import Path

# Thread lock for one-time initialization
_lock = threading.Lock()
_default_handler: Optional[logging.Handler] = None
_file_handler: Optional[logging.Handler] = None

# Supported log level mapping
log_levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

# Default log level
_default_log_level = logging.INFO
# Environment variable names
_VERBOSITY_ENV = "LOG_VERBOSITY"
_LOG_FILE_ENV = "LOG_FILE_PATH"
_DEFAULT_LOG_FILE = "./logs/app.log"


def _get_default_logging_level() -> int:
    """Get logging level from environment variable."""
    name = os.getenv(_VERBOSITY_ENV, "").lower()
    if name in log_levels:
        return log_levels[name]
    if name:
        print(
            f"Unknown {_VERBOSITY_ENV}={name}, valid options: {list(log_levels.keys())}",
            file=sys.stderr,
        )
    return _default_log_level


def _configure_root_logger() -> None:
    """Configure root logger with console and file handlers (thread-safe, once)."""
    global _default_handler, _file_handler
    with _lock:
        if _default_handler:
            return
        # Ensure stderr is available
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w")
        level = _get_default_logging_level()

        # Get root logger
        root = logging.getLogger()
        # Clear existing handlers
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Configure console output
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        root.addHandler(handler)
        root.setLevel(level)
        _default_handler = handler

        # Configure file output
        log_file_path = os.getenv(_LOG_FILE_ENV, _DEFAULT_LOG_FILE)
        if log_file_path:
            # Ensure log directory exists
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Add file handler
            try:
                _file_handler = logging.FileHandler(
                    log_file_path, encoding='utf-8')
                _file_handler.setLevel(level)
                _file_handler.setFormatter(formatter)
                root.addHandler(_file_handler)
            except Exception as e:
                print(f"Cannot create log file {log_file_path}: {e}", file=sys.stderr)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger by name, or the root logger if no name given."""
    _configure_root_logger()
    return logging.getLogger(name)


def set_verbosity(level: int) -> None:
    """Dynamically set global log level."""
    _configure_root_logger()
    root = logging.getLogger()
    root.setLevel(level)
    if _default_handler:
        _default_handler.setLevel(level)
    if _file_handler:
        _file_handler.setLevel(level)


def get_verbosity() -> int:
    """Return current global log level."""
    _configure_root_logger()
    return logging.getLogger().getEffectiveLevel()


def capture_warnings(enable: bool) -> None:
    """
    Redirect Python warnings module output to the logging system.
    """
    from logging import captureWarnings as _captureWarnings
    logger = get_logger("py.warnings")
    if _default_handler and not logger.handlers:
        logger.addHandler(_default_handler)
    if _file_handler and _file_handler not in logger.handlers:
        logger.addHandler(_file_handler)
    logger.setLevel(get_verbosity())
    _captureWarnings(enable)
