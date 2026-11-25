def __getattr__(name):
  if name == "Viewport2D":
    from .viewport_2d import Viewport2D
    return Viewport2D
  if name == "Viewport3D":
    from .viewport_3d import Viewport3D
    return Viewport3D
  raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["Viewport2D", "Viewport3D"]
