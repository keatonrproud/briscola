import logging

_LOGGING_LEVEL = logging.CRITICAL


class CustomFormatter(logging.Formatter):
    """A custom formatter for Briscola."""

    # ANSI escape codes for colors
    RESET = "\033[0m"
    RED = "\033[91m"

    def format(self, record: logging.LogRecord) -> str:
        # Apply color to critical messages
        color = self.RED if record.levelno > logging.WARNING else self.RESET

        # Format the message
        message = super().format(record)

        # Split the message into components to apply padding
        parts = message.split(":")
        if len(parts) >= 2:
            parts[0] = parts[0].ljust(40)

        message = color + "".join(parts) + self.RESET

        return message


def build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(_LOGGING_LEVEL)

    if not logger.hasHandlers():
        # Create a console handler
        console_handler = logging.StreamHandler()

        # Create and set the custom formatter
        formatter = CustomFormatter("%(name)s -- %(levelname)s:   %(message)s")
        console_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(console_handler)

    return logger
