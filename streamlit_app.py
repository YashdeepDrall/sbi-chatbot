import importlib
from pathlib import Path

from app.runtime import ui_runtime as runtime_module


module_file = Path(getattr(runtime_module, "__file__", ""))

# During local development, reload the Python module so UI edits show up
# without changing the protected release behavior that uses compiled binaries.
if module_file.suffix == ".py":
    runtime_module = importlib.reload(runtime_module)

runtime_module.run_app()
