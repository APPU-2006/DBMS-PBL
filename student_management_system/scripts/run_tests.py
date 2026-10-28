import importlib.util
import pathlib
import sys
import types

py_spec = importlib.util.find_spec("py")
if py_spec is None or py_spec.submodule_search_locations is None:
    compatibility_module = types.ModuleType("py")
    compatibility_module.path = types.SimpleNamespace(local=pathlib.Path)
    sys.modules["py"] = compatibility_module

import pytest

raise SystemExit(pytest.main())
