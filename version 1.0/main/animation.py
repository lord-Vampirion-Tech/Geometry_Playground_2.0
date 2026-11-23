import traceback


class AnimationMixin:

  def _on_frame(self):

    if not self._is_running or self.update_function is None:
      return

    elapsed_seconds = (
        self._clock.nsecsElapsed() / 1_000_000_000
    )

    current_time = self._time_base + elapsed_seconds

    try:

      self._call_update(current_time)

      self.status.setText(
          f"Воспроизведение | Объектов: {len(self.objects)}"
      )

    except Exception as error:

      self._show_code_error(error)
      self._stop_playback()
      self.status.setText("Ошибка в update(Time)")

      print(traceback.format_exc())

  def toggle_pause(self):

    if self.update_function is None:
      return

    if self._is_running:

      elapsed_seconds = (
          self._clock.nsecsElapsed() / 1_000_000_000
      )

      current_time = self._time_base + elapsed_seconds

      self.frame_timer.stop()
      self._is_running = False

      try:

        self._call_update(current_time)

      except Exception:

        self._stop_playback()

        self.status.setText("Ошибка в update(Time)")

        print(traceback.format_exc())

        return

      self._time_base = self.Time

      self.btn_pause.setText("▶ Продолжить")
      self.status.setText("Пауза")

    else:

      self._time_base = self.Time

      self._clock.start()
      self._is_running = True

      self.frame_timer.start()

      self.btn_pause.setText("Ⅱ Пауза")
      self.status.setText("Воспроизведение")

  def closeEvent(self, event):

    self.frame_timer.stop()

    self.plotter.close()

    super().closeEvent(event)
