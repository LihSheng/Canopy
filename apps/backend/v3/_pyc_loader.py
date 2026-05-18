from importlib.util import module_from_spec, spec_from_loader
from importlib.machinery import SourcelessFileLoader
from pathlib import Path


def load_pyc_namespace(namespace: dict, relative_pyc_path: str) -> None:
    pyc_path = Path(__file__).resolve().parent / relative_pyc_path
    loader = SourcelessFileLoader(namespace["__name__"], str(pyc_path))
    spec = spec_from_loader(namespace["__name__"], loader)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load bytecode module: {pyc_path}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    for key, value in module.__dict__.items():
        if key in {"__name__", "__loader__", "__package__", "__spec__"}:
            continue
        namespace[key] = value
