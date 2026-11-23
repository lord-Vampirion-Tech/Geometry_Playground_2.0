import math
import traceback

from shapes import Square
from shapes3d import Cube, BoundingCube


class SceneMixin:

  def toggle_mode(self):

    if self.mode == "2D":

      self.mode = "3D"

      self.view_stack.setCurrentWidget(self.plotter)

      self.btn_mode.setText("Перейти в 2D")

    else:

      self.mode = "2D"

      self.view_stack.setCurrentWidget(self.graph)

      self.btn_mode.setText("Перейти в 3D")

    self.run_code()

  @staticmethod
  def _loop(value, duration, start=0.0):

    duration = float(duration)
    start = float(start)
    value = float(value)

    if duration <= 0:
      raise ValueError(
          "duration в loop() должен быть больше нуля"
      )

    return start + ((value - start) % duration)

  def _create_namespace(self, new_objects):

    def New_SQUAER(
        x=0,
        y=0,
        width=16,
        height=16,
        color="#42a5f5"
    ):

      square = Square(
          x=x,
          y=y,
          width=width,
          height=height,
          color=color
      )

      new_objects.append(square)

      return square

    def New_CUBE(
        x=0,
        y=0,
        z=0,
        width=16,
        height=16,
        depth=16,
        color="#42a5f5",
        opacity=1.0
    ):

      cube = Cube(
          x=x,
          y=y,
          z=z,
          width=width,
          height=height,
          depth=depth,
          color=color,
          opacity=opacity
      )

      new_objects.append(cube)

      return cube

    def New_BOUNDS(
        minx,
        miny,
        minz,
        maxx,
        maxy,
        maxz,
        color="#42a5f5",
        opacity=1.0
    ):

      cube = BoundingCube(
          minx=minx,
          miny=miny,
          minz=minz,
          maxx=maxx,
          maxy=maxy,
          maxz=maxz,
          color=color,
          opacity=opacity
      )

      new_objects.append(cube)

      return cube

    math_functions = {
        name: getattr(math, name)
        for name in dir(math)
        if not name.startswith("_")
    }

    namespace = {
        "New_SQUAER": New_SQUAER,
        "New_CUBE": New_CUBE,
        "New_BOUNDS": New_BOUNDS,
        "math": math,
        "Time": 0.0,
        "loop": self._loop,
        **math_functions
    }

    namespace["arccos"] = math.acos
    namespace["arcsin"] = math.asin
    namespace["arctan"] = math.atan

    return namespace

  def _set_time(self, value):

    self.Time = float(value)

    self.time_label.setText(
        f"Time: {self.Time:.3f} s"
    )

    if self.namespace:
      self.namespace["Time"] = self.Time

  def _visible_objects(self):

    if self.mode == "2D":
      return [
          obj for obj in self.objects
          if isinstance(obj, Square)
      ]

    return [
        obj for obj in self.objects
        if isinstance(obj, (Cube, BoundingCube))
    ]

  def _update_scene(self):

    for obj in self._visible_objects():
      obj.update_draw()

    if self.mode == "3D":
      self.plotter.render()

  def _call_update(self, value):

    self._set_time(value)

    if self.update_function is not None:
      self.update_function(self.Time)

    self._update_scene()

  def _stop_playback(self):

    self.frame_timer.stop()

    self._is_running = False
    self.update_function = None

    self.btn_pause.setEnabled(False)
    self.btn_pause.setText("Ⅱ Пауза")

  def run_code(self):

    self._stop_playback()

    self.editor.clear_error()

    self._set_time(0.0)
    self._time_base = 0.0

    new_objects = []

    namespace = self._create_namespace(new_objects)

    source = self.editor.toPlainText()

    self.status.setText("Выполнение...")

    try:

      exec(source, namespace, namespace)

      update_function = namespace.get("update")

      if update_function is not None and not callable(update_function):

        raise TypeError(
            "update должна быть функцией: def update(Time):"
        )

      if update_function is not None:

        namespace["Time"] = 0.0
        update_function(0.0)

      # Сохраняем состояние камеры до очистки сцены.
      camera_state = None

      if self._camera_initialized:
        camera_state = self._save_camera_state()

      # Обновляем 2D-сцену.
      self.graph.clear()
      self._configure_2d_graph()

      # Обновляем 3D-сцену.
      self.plotter.clear()
      self._configure_3d_scene()

      self.objects = new_objects
      self.namespace = namespace
      self.update_function = update_function

      # Отрисовываем объекты текущего режима.
      for obj in self._visible_objects():

        if self.mode == "2D":
          obj.draw(self.graph)

        else:
          obj.draw(self.plotter)

      # Восстанавливаем камеру независимо от текущего режима.
      if camera_state is not None:

        self._restore_camera_state(camera_state)

      elif self.mode == "3D":

        self._reset_3d_camera()
        self._camera_initialized = True

      self._set_time(0.0)

      if self.update_function is not None:

        self._time_base = 0.0

        self._clock.start()
        self._is_running = True

        self.frame_timer.start()

        self.btn_pause.setEnabled(True)
        self.btn_pause.setText("Ⅱ Пауза")

        self.status.setText(
            f"Анимация запущена | Объектов: {len(self.objects)}"
        )

      else:

        self.btn_pause.setEnabled(False)

        self.status.setText(
            f"Готово | Статичная сцена | Объектов: {len(self.objects)}"
        )

    except Exception as error:

      self._show_code_error(error)
      self._stop_playback()
      self.status.setText("Ошибка выполнения")

      print(traceback.format_exc())
