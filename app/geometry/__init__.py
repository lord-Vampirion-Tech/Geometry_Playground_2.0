from importlib import import_module


_EXPORTS = {
    "Point": ("three_d", "Point"),
    "Line": ("three_d", "Line"),
    "Point2D": ("two_d", "Point"),
    "Line2D": ("two_d", "Line"),
    "Point3D": ("three_d", "Point"),
    "Line3D": ("three_d", "Line"),
    "Square": ("two_d", "Square"),
    "Polygon": ("two_d", "Polygon"),
    "Circle": ("two_d", "Circle"),
    "Cube": ("three_d", "Cube"),
    "BoundingCube": ("three_d", "BoundingCube"),
    "Sphere": ("three_d", "Sphere"),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    package, attribute = target
    module = import_module(f".{package}", __name__)
    value = getattr(module, attribute)
    globals()[name] = value
    return value
