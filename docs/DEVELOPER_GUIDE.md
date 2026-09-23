# Developer Guide

## Prerequisites

- Python 3.10+ recommended.
- A pfSense VM for live testing.
- SSH access to the VM.
- A benchmark PDF supplied by the administrator.
- Optional Gemini API key if AI features are enabled.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For the optional Gemini integration:

```bash
pip install -r requirements-gemini.txt
```

Set environment variables as required by `backend/core/settings.py` and the AI client. Never commit real credentials.

## Run

The entry point is `app.py`. The Flask application is created through `backend/app_factory.py` and routes are registered through the modular API package.

Use a development server for local work only. For a deployment environment, place the application behind an appropriate WSGI server and network controls.

## Test

```bash
pytest -q
```

The tests include modular structure checks, compliance behavior, and pfSense engine-related tests. Live SSH functionality requires a real pfSense environment and is not fully testable inside the development sandbox.

## Development rule

A module should expose a small, stable interface. Avoid importing another module's internal classes when a shared contract or service boundary already exists.

## Adding a module

1. Create the module directory.
2. Define its responsibility.
3. Add or reuse a shared contract.
4. Add unit tests.
5. Add an API route only if external access is required.
6. Update the architecture and extension documentation.
7. Do not place module-specific state in `app.py`.
