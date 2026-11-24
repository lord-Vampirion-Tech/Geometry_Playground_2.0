import math
from time import perf_counter_ns

import numpy as np
import pyvista as pv
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
        self.last_geometry_ms = 0.0
        self.last_render_ms = 0.0
        self.last_apply_ms = 0.0
        self.last_property_ms = 0.0
        self.last_updated_objects = 0
        self.last_pending_count = 0
        self._create_fps_counter()

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

    def _create_fps_counter(self):
        self._fps_actor = self.plotter.add_text(
            "FPS: --", position="upper_right", font_size=10,
            color="#d7e0ea", name="fps_counter"
        )

    def set_fps(self, value, script_ms=None):
        script_text = (
            f" | Python: {script_ms:.1f} ms"
            if script_ms is not None else ""
        )
        self.plotter.add_text(
            f"FPS: {value:.0f}{script_text}"
            f" | Geometry: {self.last_geometry_ms:.1f} ms"
            f" | Render: {self.last_render_ms:.1f} ms",
            position="upper_right",
            font_size=10,
            color="#d7e0ea",
            name="fps_counter"
        )

    def set_performance_stats(self, stats):
        text = (
            f"FPS {stats['fps']:.0f} | Interval {stats['interval_ms']:.1f} ms "
            f"(p95 {stats['interval_p95_ms']:.1f})\\n"
            f"Frame {stats['frame_ms']:.1f} ms (p95 {stats['frame_p95_ms']:.1f}) "
            f"| Wait/Qt {stats['wait_ms']:.1f} ms\\n"
            f"Python {stats['script_ms']:.2f} | Apply {stats['apply_ms']:.2f} "
            f"(geom {stats['geometry_ms']:.2f}, props {stats['properties_ms']:.2f}) "
            f"| Render {stats['render_ms']:.2f} ms\\n"
            f"Objects {stats['objects']} | Updated {stats['updated']} "
            f"| Pending {stats['pending']}"
        )
        self.plotter.add_text(
            text,
            position="upper_right",
            font_size=9,
            color="#d7e0ea",
            name="fps_counter"
        )

    def begin_update(self):
        if self._render_batch_depth == 0:
            self.last_geometry_ms = 0.0
            self.last_render_ms = 0.0
            self.last_apply_ms = 0.0
            self.last_property_ms = 0.0
            self.last_updated_objects = 0
            self.last_pending_count = 0
        self._render_batch_depth += 1

    def end_update(self):
        if self._render_batch_depth <= 0:
            return

        self._render_batch_depth -= 1
        if self._render_batch_depth != 0:
            return

        if self._pending_object_updates:
            pending = tuple(self._pending_object_updates.values())
            self.last_pending_count = len(pending)
            self._pending_object_updates.clear()
            for obj, actor in pending:
                self._apply_object_update(obj, actor)

        if self._render_pending:
            self._render_pending = False
            start = perf_counter_ns()
            self.plotter.render()
            self.last_render_ms = (perf_counter_ns() - start) / 1_000_000

    def add_object(self, obj):
        actor = self.plotter.add_mesh(
            obj.to_polydata(),
            color=obj.color,
            opacity=obj.opacity,
            show_edges=not hasattr(obj, "RADIUS"),
            edge_color="#ffffff",
            line_width=1,
            render=False
        )

        if hasattr(obj, "RADIUS"):
            actor.SetPosition(obj.x, obj.y, obj.z)

            if obj.name:
                label_data = pv.PolyData(
                    np.array([[obj.x, obj.y, obj.z]], dtype=np.float64)
                )
                label_data.point_data["labels"] = [obj.name]
                label = self.plotter.add_point_labels(
                    label_data,
                    "labels",
                    show_points=False,
                    shape=None,
                    name=f"point_label_{id(obj)}",
                    render=False
                )
                result = (actor, label, label_data)
            else:
                result = actor
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
        render_start = perf_counter_ns()
        self.plotter.render()
        self.last_render_ms = (perf_counter_ns() - render_start) / 1_000_000

    def _apply_object_update(self, obj, actor):
        mesh_actor = actor[0] if isinstance(actor, tuple) else actor
        apply_start = perf_counter_ns()
        geometry_start = apply_start

        if hasattr(obj, "RADIUS"):
            mesh_actor.SetPosition(obj.x, obj.y, obj.z)

            if isinstance(actor, tuple) and len(actor) > 2:
                label_data = actor[2]
                label_points = label_data.GetPoints()
                label_points.SetPoint(0, obj.x, obj.y, obj.z)
                label_points.GetData().Modified()
                label_points.Modified()
                label_data.Modified()
        else:
            obj.to_polydata()

        geometry_end = perf_counter_ns()
        self.last_geometry_ms += (geometry_end - geometry_start) / 1_000_000

        property_start = perf_counter_ns()
        mesh_actor.prop.color = obj.color
        mesh_actor.prop.opacity = obj.opacity
        property_end = perf_counter_ns()

        self.last_property_ms += (property_end - property_start) / 1_000_000
        self.last_apply_ms += (property_end - apply_start) / 1_000_000
        self.last_updated_objects += 1

    def clear_scene(self):
        camera_state = self._save_camera_state() if self._camera_initialized else None

        self.plotter.clear()
        self.plotter.set_background("#20232b")
        self.plotter.add_axes()
        self._create_floor(size=1000, step=10)
        self._create_fps_counter()

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
