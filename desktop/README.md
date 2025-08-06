# Coin Maker Desktop

Desktop application coordinator for Coin Maker - manages backend/frontend integration and GUI wrapper for standalone desktop use.

## Architecture

This module:
- Depends on `../backend` as a path dependency (inherits all backend functionality)
- Adds desktop-specific services (PyWebView, port management, SvelteKit coordination)
- Provides desktop entry points and GUI wrappers

## Development

```bash
# Install dependencies (includes backend via path dependency)
poetry install

# Run desktop application
poetry run python desktop_main.py

# Type checking
poetry run pyright

# Linting
poetry run ruff check .
poetry run ruff format .

# Testing
poetry run pytest
```

## Dependencies

- **Backend**: All core functionality via path dependency to `../backend`
- **Desktop GUI**: PyWebView, PyQt6 for native desktop integration
- **Development**: Independent dev tools (pyright, ruff, pytest)

## Entry Points

- `desktop_main.py`: Main desktop application entry point
- `desktop_app.py`: DesktopApp class - coordinates backend/frontend/GUI