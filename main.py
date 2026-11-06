"""Main entry point for Social Media Automation Architecture."""
import sys

# Ensure UTF-8 output encoding across Windows shells
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from cli import cli

if __name__ == "__main__":
    cli()
