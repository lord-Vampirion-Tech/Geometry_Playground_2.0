import math

import numpy as np
import pyvista as pv
from vtkmodules.vtkRenderingCore import vtkBillboardTextActor3D
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from pyvistaqt import QtInteractor


class Viewport3D(QWidget):
  def __init__(self, parent=None):
    super().__init__(parent)

    layout = QVBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)

    self.plotter = QtInteractor(self, auto_update=False)
    layout.addWidget(self.plotter)

    self.plotter.set_background("#20232b")
    self.plotter.add_axes()
    self._create_floor(size=1000, step=10)
    self.plotter.camera_position = "iso"
    self.plotter.camera.SetViewUp(0, 1, 0)
    self.plotter.camera.OrthogonalizeViewUp()

    self._camera_drag_mode = None
    self._last_mouse_pos = None
    self._camera_initialized = True
    self._render_batch_depth = 0
    self._render_pending = False
    self._pending_object_updates = {}

    self.plotter.installEventFilter(self)
    self.plotter.setFocusPolicy(Qt.StrongFocus)


  def _create_floor(self, size=1000, step=10):
    half = size / 2

    points = []
    lines = []

    def add_line(start, end):
      index = len(points)
      points.extend((start, end))
      lines.extend((2, index, index + 1))

    count = int(size / step)

    for i in range(count + 1):
      pos = -half + i * step
      add_line((-half, 0, pos), (half, 0, pos))
      add_line((pos, 0, -half), (pos, 0, half))

    grid = pv.PolyData(
        np.asarray(points, dtype=np.float32),
        lines=np.asarray(lines, dtype=np.int64)
    )

    self.plotter.add_mesh(
        grid,
        color="#414956",
        line_width=1,
        lighting=False,
        name="world_grid"
    )

    self.plotter.add_mesh(
        pv.Line((-half, 0, 0), (half, 0, 0)),
        color="#d65b5b",
        line_width=2,
        lighting=False,
        name="world_axis_x"
    )

    self.plotter.add_mesh(
        pv.Line((0, 0, -half), (0, 0, half)),
        color="#5b91d6",
        line_width=2,
        lighting=False,
        name="world_axis_z"
    )

    self.plotter.add_mesh(
        pv.Line((0, -half, 0), (0, half, 0)),
        color="#65c878",
        line_width=2,
        lighting=False,
        name="world_axis_y"
    )

  def begin_update(self):
    self._render_batch_depth += 1

  def end_update(self):
    if self._render_batch_depth <= 0:
      return

    self._render_batch_depth -= 1
    if self._render_batch_depth != 0:
      return

    if self._pending_object_updates:
      pending = tuple(self._pending_object_updates.values())
      self._pending_object_updates.clear()
      for obj, actor in pending:
        self._apply_object_update(obj, actor)

    if self._render_pending:
      self._render_pending = False
      self.plotter.render()

  def add_object(self, obj):
    is_point = obj.__class__.__name__ == "Point"
    actor = self.plotter.add_mesh(
        obj.to_polydata(),
        color=obj.color,
        opacity=obj.opacity,
        show_edges=not is_point and obj.__class__.__name__ in {"Cube", "BoundingCube", "Sphere"},
        edge_color="#ffffff",
        line_width=getattr(obj, "line_width", 1),
        render=False
    )
    outline_actor = None
    if is_point:
      outline_mesh = pv.Sphere(
          radius=1.06,
          center=(0.0, 0.0, 0.0),
          theta_resolution=20,
          phi_resolution=20
      )
      outline_actor = self.plotter.add_mesh(
          outline_mesh,
          color="#ffffff",
          opacity=obj.opacity,
          smooth_shading=True,
          render=False
      )

    if getattr(obj, "SCALE_GEOMETRY", False):
      actor.SetScale(obj.radius, obj.radius, obj.radius)

    if hasattr(obj, "RADIUS"):
      actor.SetPosition(obj.x, obj.y, obj.z)
      if outline_actor is not None:
        outline_actor.SetPosition(obj.x, obj.y, obj.z)

      if getattr(obj, "name", None):
        label = vtkBillboardTextActor3D()
        label.SetInput(str(obj.name))
        label.SetPosition(obj.x, obj.y, obj.z)
        label.GetTextProperty().SetColor(0.92, 0.93, 0.96)
        label.GetTextProperty().SetFontSize(16)
        self.plotter.renderer.AddActor(label)
        result = (
            (actor, outline_actor, label)
            if outline_actor is not None
            else (actor, label)
        )
      else:
        result = (actor, outline_actor) if outline_actor is not None else actor
    else:
      result = actor

    if self._render_batch_depth:
      self._render_pending = True
    else:
      self.plotter.render()

    return result

  def update_object(self, obj, actor):
    if self._render_batch_depth:
      self._pending_object_updates[id(obj)] = (obj, actor)
      self._render_pending = True
      return

    self._apply_object_update(obj, actor)
    self.plotter.render()

  def _apply_object_update(self, obj, actor):
    mesh_actor = actor[0] if isinstance(actor, tuple) else actor

    if hasattr(obj, "RADIUS"):
      mesh_actor.SetPosition(obj.x, obj.y, obj.z)
      if isinstance(actor, tuple):
        if obj.__class__.__name__ == "Point":
          if len(actor) > 1 and actor[1] is not None:
            actor[1].SetPosition(obj.x, obj.y, obj.z)
            actor[1].prop.opacity = getattr(obj, "opacity", 1.0)
          if len(actor) > 2 and actor[2] is not None:
            actor[2].SetPosition(obj.x, obj.y, obj.z)
            actor[2].GetTextProperty().SetOpacity(
                getattr(obj, "opacity", 1.0)
            )
        elif len(actor) > 1 and actor[1] is not None:
          actor[1].SetPosition(obj.x, obj.y, obj.z)
          actor[1].GetTextProperty().SetOpacity(
              getattr(obj, "opacity", 1.0)
          )

      if getattr(obj, "SCALE_GEOMETRY", False):
        mesh_actor.SetScale(obj.radius, obj.radius, obj.radius)
    else:
      obj.to_polydata()

    mesh_actor.prop.color = obj.color
    mesh_actor.prop.opacity = getattr(obj, "opacity", 1.0)
    if hasattr(obj, "line_width"):
      mesh_actor.prop.line_width = obj.line_width

  def clear_scene(self):
    camera_state = self._save_camera_state() if self._camera_initialized else None

    self.plotter.clear()
    self.plotter.set_background("#20232b")
    self.plotter.add_axes()
    self._create_floor(size=1000, step=10)

    if camera_state is not None:
      self._restore_camera_state(camera_state)
    else:
      self.plotter.view_isometric()
      self._camera_initialized = True

    self.plotter.render()

  def _save_camera_state(self):
    camera = self.plotter.camera
    return {
        "position": camera.GetPosition(),
        "focal_point": camera.GetFocalPoint(),
        "view_up": camera.GetViewUp(),
        "view_angle": camera.GetViewAngle(),
        "parallel_projection": camera.GetParallelProjection(),
        "parallel_scale": camera.GetParallelScale(),
        "window_center": camera.GetWindowCenter()
    }

  def _restore_camera_state(self, state):
    camera = self.plotter.camera
    camera.SetPosition(*state["position"])
    camera.SetFocalPoint(*state["focal_point"])
    camera.SetViewUp(*state["view_up"])
    camera.SetViewAngle(state["view_angle"])
    camera.SetParallelProjection(state["parallel_projection"])
    camera.SetParallelScale(state["parallel_scale"])
    camera.SetWindowCenter(*state["window_center"])
    self._update_camera()

  def _update_camera(self):
    self.plotter.renderer.ResetCameraClippingRange()
    self.plotter.render()

  def eventFilter(self, watched, event):
    if watched is not self.plotter:
      return super().eventFilter(watched, event)

    event_type = event.type()

    if event_type == QEvent.Type.MouseButtonPress:
      button = event.button()

      if button == Qt.MouseButton.LeftButton:
        self._camera_drag_mode = "orbit"
      elif button == Qt.MouseButton.MiddleButton:
        self._camera_drag_mode = "pan"
      elif button == Qt.MouseButton.RightButton:
        self._camera_drag_mode = "zoom"
      else:
        return super().eventFilter(watched, event)

      self._last_mouse_pos = event.position().toPoint()
      self.plotter.setFocus()
      return True

    if event_type == QEvent.Type.MouseButtonRelease:
      if event.button() in (
          Qt.MouseButton.LeftButton,
          Qt.MouseButton.MiddleButton,
          Qt.MouseButton.RightButton
      ):
        self._camera_drag_mode = None
        self._last_mouse_pos = None
        return True

    if event_type == QEvent.Type.MouseMove and self._camera_drag_mode:
      current_pos = event.position().toPoint()

      if self._last_mouse_pos is not None:
        dx = current_pos.x() - self._last_mouse_pos.x()
        dy = current_pos.y() - self._last_mouse_pos.y()

        if self._camera_drag_mode == "orbit":
          self._orbit_camera(dx, dy)
        elif self._camera_drag_mode == "pan":
          self._pan_camera(dx, dy)
        elif self._camera_drag_mode == "zoom":
          self._zoom_camera(dy)

      self._last_mouse_pos = current_pos
      return True

    if event_type == QEvent.Type.Wheel:
      delta = event.angleDelta().y()
      if delta:
        self._zoom_camera(-delta / 120 * 35)
        return True

    if event_type == QEvent.Type.KeyPress:
      key = event.key()
      movement_keys = (
          Qt.Key.Key_W, Qt.Key.Key_A, Qt.Key.Key_S,
          Qt.Key.Key_D, Qt.Key.Key_Q, Qt.Key.Key_E
      )

      if key in movement_keys:
        fast = bool(
            QApplication.keyboardModifiers()
            & Qt.KeyboardModifier.ShiftModifier
        )
        self._move_camera(key, fast)
        return True

    return super().eventFilter(watched, event)

  def _orbit_camera(self, dx, dy):
    camera = self.plotter.camera
    position = np.array(camera.GetPosition(), dtype=float)
    focal_point = np.array(camera.GetFocalPoint(), dtype=float)

    offset = position - focal_point
    distance = np.linalg.norm(offset)
    if distance < 1e-8:
      return

    sensitivity = 0.35
    yaw = math.radians(-dx * sensitivity)
    pitch_delta = math.radians(-dy * sensitivity)

    cos_yaw, sin_yaw = math.cos(yaw), math.sin(yaw)
    x = offset[0] * cos_yaw - offset[2] * sin_yaw
    z = offset[0] * sin_yaw + offset[2] * cos_yaw
    offset[0], offset[2] = x, z

    elevation = math.asin(np.clip(offset[1] / distance, -1.0, 1.0))
    elevation = np.clip(
        elevation + pitch_delta,
        math.radians(-89.5),
        math.radians(89.5)
    )

    horizontal = math.hypot(offset[0], offset[2])
    if horizontal < 1e-8:
      return

    direction = np.array([
        offset[0] / horizontal, 0.0, offset[2] / horizontal
    ])
    horizontal_distance = distance * math.cos(elevation)
    offset = (
        direction * horizontal_distance
        + np.array([0.0, distance * math.sin(elevation), 0.0])
    )

    camera.SetPosition(focal_point + offset)
    camera.SetViewUp(0, 1, 0)
    camera.OrthogonalizeViewUp()
    self._update_camera()

  def _pan_camera(self, dx, dy):
    camera = self.plotter.camera
    position = np.array(camera.GetPosition(), dtype=float)
    focal_point = np.array(camera.GetFocalPoint(), dtype=float)

    forward = focal_point - position
    distance = np.linalg.norm(forward)
    if distance < 1e-8:
      return
    forward /= distance

    world_up = np.array([0.0, 1.0, 0.0])
    right = np.cross(forward, world_up)
    right_length = np.linalg.norm(right)
    if right_length < 1e-8:
      return
    right /= right_length

    up = np.cross(right, forward)
    up /= np.linalg.norm(up)

    scale = distance * 0.0015
    movement = right * (-dx * scale) + up * (dy * scale)

    camera.SetPosition(position + movement)
    camera.SetFocalPoint(focal_point + movement)
    self._update_camera()

  def _zoom_camera(self, dy):
    camera = self.plotter.camera
    position = np.array(camera.GetPosition(), dtype=float)
    focal_point = np.array(camera.GetFocalPoint(), dtype=float)

    offset = position - focal_point
    distance = np.linalg.norm(offset)
    if distance < 1e-8:
      return

    new_distance = float(np.clip(
        distance * math.exp(dy * 0.01),
        0.05,
        1_000_000.0
    ))

    camera.SetPosition(focal_point + offset / distance * new_distance)
    camera.SetViewUp(0, 1, 0)
    camera.OrthogonalizeViewUp()
    self._update_camera()

  def _move_camera(self, key, fast=False):
    camera = self.plotter.camera
    position = np.array(camera.GetPosition(), dtype=float)
    focal_point = np.array(camera.GetFocalPoint(), dtype=float)
    view_up = np.array(camera.GetViewUp(), dtype=float)

    forward = focal_point - position
    distance = np.linalg.norm(forward)
    if distance < 1e-8:
      return
    forward /= distance

    right = np.cross(forward, view_up)
    right_length = np.linalg.norm(right)
    if right_length < 1e-8:
      return
    right /= right_length

    speed = max(distance * 0.08, 0.1)
    if fast:
      speed *= 3

    movement = np.zeros(3)

    if key == Qt.Key.Key_W:
      movement += forward * speed
    elif key == Qt.Key.Key_S:
      movement -= forward * speed
    elif key == Qt.Key.Key_A:
      movement -= right * speed
    elif key == Qt.Key.Key_D:
      movement += right * speed
    elif key == Qt.Key.Key_Q:
      movement -= np.array([0.0, 1.0, 0.0]) * speed
    elif key == Qt.Key.Key_E:
      movement += np.array([0.0, 1.0, 0.0]) * speed

    camera.SetPosition(position + movement)
    camera.SetFocalPoint(focal_point + movement)
    self._update_camera()

  def closeEvent(self, event):
    self.plotter.close()
    super().closeEvent(event)
