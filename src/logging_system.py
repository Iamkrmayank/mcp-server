"""
Comprehensive Logging System
Tracks all system events with precise timestamps, metrics, and data quality indicators.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path
import os


class AgnoLogger:
    """Enhanced logging system for the Agno orchestration framework."""
    
    def __init__(self, log_file: str = "agno_system.log", log_level: str = "INFO"):
        """
        Initialize the logging system.
        
        Args:
            log_file: Path to the log file
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger("AgnoSystem")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def _get_utc_timestamp(self) -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
    
    def log_operation(
        self,
        operation_name: str,
        status: str,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        data_quality: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log a system operation with comprehensive details.
        
        Args:
            operation_name: Name of the operation (e.g., "Tavily_Request")
            status: Status of the operation ("success", "failure", "in_progress")
            duration_ms: Execution duration in milliseconds
            error_message: Error message if applicable
            data_quality: Quality metrics (confidence, completeness, etc.)
            metadata: Additional metadata
            
        Returns:
            Dictionary containing the logged information
        """
        log_entry = {
            "timestamp": self._get_utc_timestamp(),
            "operation": operation_name,
            "status": status,
            "duration_ms": duration_ms,
            "error": error_message,
            "data_quality": data_quality or {},
            "metadata": metadata or {}
        }
        
        # Format log message
        log_msg = f"[{operation_name}] Status: {status}"
        if duration_ms is not None:
            log_msg += f" | Duration: {duration_ms:.2f}ms"
        if error_message:
            log_msg += f" | Error: {error_message}"
        if data_quality:
            log_msg += f" | Quality: {json.dumps(data_quality)}"
        
        # Log at appropriate level
        if status == "failure":
            self.logger.error(log_msg)
        elif status == "success":
            self.logger.info(log_msg)
        else:
            self.logger.debug(log_msg)
        
        return log_entry
    
    def log_request_start(self, operation_name: str, input_data: Optional[Dict[str, Any]] = None):
        """Log the start of a request."""
        metadata = {"input": input_data} if input_data else {}
        return self.log_operation(
            operation_name=f"{operation_name}_Start",
            status="in_progress",
            metadata=metadata
        )
    
    def log_request_end(
        self,
        operation_name: str,
        success: bool,
        duration_ms: float,
        error: Optional[str] = None,
        data_quality: Optional[Dict[str, Any]] = None
    ):
        """Log the end of a request with results."""
        return self.log_operation(
            operation_name=f"{operation_name}_End",
            status="success" if success else "failure",
            duration_ms=duration_ms,
            error_message=error,
            data_quality=data_quality
        )
    
    def log_fallback(self, from_tool: str, to_tool: str, reason: str):
        """Log a fallback event."""
        return self.log_operation(
            operation_name="Fallback_Triggered",
            status="in_progress",
            metadata={
                "from": from_tool,
                "to": to_tool,
                "reason": reason
            }
        )
    
    def info(self, message: str):
        """Log an info message."""
        self.logger.info(message)
    
    def error(self, message: str):
        """Log an error message."""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)


# Global logger instance
_logger_instance: Optional[AgnoLogger] = None


def get_logger() -> AgnoLogger:
    """Get or create the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        log_file = os.getenv("LOG_FILE", "agno_system.log")
        log_level = os.getenv("LOG_LEVEL", "INFO")
        _logger_instance = AgnoLogger(log_file=log_file, log_level=log_level)
    return _logger_instance

