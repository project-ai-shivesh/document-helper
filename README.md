# LangChain Documentation Helper

## Setup with UV

This project uses [UV](https://github.com/astral-sh/uv) for dependency management.

### Installation

First, ensure you have UV installed. Then, to set up the project:

```bash
uv sync
```

This will create a virtual environment and install all dependencies.

### Running the project

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Or use UV to run commands directly:

```bash
uv run python ingestion.py
```

### Installing additional dev dependencies

If you need to install dev dependencies:

```bash
uv sync --group dev
```

### Updating dependencies

To update all dependencies to their latest versions:

```bash
uv lock --upgrade
uv sync
```

To update a specific package:

```bash
uv lock --upgrade-package <package-name>
uv sync
```
