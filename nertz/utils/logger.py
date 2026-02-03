class Logger:
    verbose: bool

    def log(self, message: str, *, level: str = "INFO") -> None:
        """Centralized logging helper (stdout for now)."""
        print(f"[{level}] {message}")

    def log_debug(self, message: str) -> None:
        if self.verbose:
            self.log(message, level="DEBUG")