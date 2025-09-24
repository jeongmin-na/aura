"""
Logging utilities for the DLD to Cursor AI Prompt Generation System
"""

import logging
import sys
from typing import Optional
from pathlib import Path
import colorlog

def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_color: bool = True
) -> logging.Logger:
    """
    Set up a logger with both console and file handlers
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        enable_color: Enable colored console output
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    if enable_color:
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

class AgentLogger:
    """Logger wrapper for agents with context tracking"""
    
    def __init__(self, agent_name: str, logger: Optional[logging.Logger] = None):
        self.agent_name = agent_name
        self.logger = logger or setup_logger(f"agent.{agent_name}")
        self.context_stack = []
    
    def push_context(self, context: str) -> None:
        """Push context to the stack"""
        self.context_stack.append(context)
    
    def pop_context(self) -> Optional[str]:
        """Pop context from the stack"""
        return self.context_stack.pop() if self.context_stack else None
    
    def _format_message(self, message: str) -> str:
        """Format message with context"""
        if self.context_stack:
            context_str = " -> ".join(self.context_stack)
            return f"[{context_str}] {message}"
        return message
    
    def debug(self, message: str, **kwargs) -> None:
        self.logger.debug(self._format_message(message), **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        self.logger.info(self._format_message(message), **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        self.logger.warning(self._format_message(message), **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        self.logger.error(self._format_message(message), **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        self.logger.critical(self._format_message(message), **kwargs)

# Performance logging utilities
class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_agent_performance(
        self,
        agent_name: str,
        operation: str,
        duration: float,
        success: bool,
        metrics: dict = None
    ) -> None:
        """Log agent performance metrics"""
        metrics = metrics or {}
        
        self.logger.info(
            f"Agent Performance - {agent_name}.{operation}: "
            f"duration={duration:.2f}s, success={success}, metrics={metrics}"
        )
    
    def log_system_metrics(self, metrics: dict) -> None:
        """Log system-wide metrics"""
        self.logger.info(f"System Metrics: {metrics}")
    
    def log_quality_metrics(self, agent_name: str, quality_scores: dict) -> None:
        """Log quality assessment metrics"""
        self.logger.info(f"Quality Metrics - {agent_name}: {quality_scores}")
