"""Command modules for vidio-cli."""

import pkgutil
from importlib import import_module
from pathlib import Path
from typing import Callable


def get_commands() -> dict[str, Callable]:
    """
    Dynamically discover and import all command modules in this package.

    Returns:
        A dictionary mapping command names to functions.
    """
    commands = {}

    # Get the directory of this package
    package_dir = Path(__file__).parent

    # Find all Python modules in this package
    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        # Skip the __init__ module
        if module_name == "__init__":
            continue

        # Import the module
        module = import_module(f"{__package__}.{module_name}")

        # Look for a 'register' function
        if hasattr(module, "register"):
            # This is a valid command module, add it to the dict
            command_name = module_name.replace("_", "-")
            commands[command_name] = module.register

    return commands
