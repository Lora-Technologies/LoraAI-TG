import logging
import json
import sys
from datetime import datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "chat_id"):
            log_data["chat_id"] = record.chat_id
        if hasattr(record, "action"):
            log_data["action"] = record.action
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class BotLogger(logging.Logger):
    def _log_with_context(
        self, 
        level: int, 
        msg: str, 
        user_id: int = None,
        chat_id: int = None,
        action: str = None,
        extra_data: dict = None,
        **kwargs
    ) -> None:
        extra = kwargs.get("extra", {})
        if user_id:
            extra["user_id"] = user_id
        if chat_id:
            extra["chat_id"] = chat_id
        if action:
            extra["action"] = action
        if extra_data:
            extra["extra_data"] = extra_data
        kwargs["extra"] = extra
        super().log(level, msg, **kwargs)
    
    def info_ctx(self, msg: str, **kwargs) -> None:
        self._log_with_context(logging.INFO, msg, **kwargs)
    
    def warning_ctx(self, msg: str, **kwargs) -> None:
        self._log_with_context(logging.WARNING, msg, **kwargs)
    
    def error_ctx(self, msg: str, **kwargs) -> None:
        self._log_with_context(logging.ERROR, msg, **kwargs)
    
    def debug_ctx(self, msg: str, **kwargs) -> None:
        self._log_with_context(logging.DEBUG, msg, **kwargs)


logging.setLoggerClass(BotLogger)

_loggers: dict[str, BotLogger] = {}


def setup_logger(name: str = "bot", level: str = "INFO") -> BotLogger:
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    
    logger.propagate = False
    _loggers[name] = logger
    return logger


def get_logger(name: str = "bot") -> BotLogger:
    if name not in _loggers:
        return setup_logger(name)
    return _loggers[name]
