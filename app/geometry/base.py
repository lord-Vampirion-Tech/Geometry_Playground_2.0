class Drawable:
    def __init__(self, draw_callback=None, update_callback=None):
        self._draw_callback = draw_callback
        self._update_callback = update_callback
        self._drawn = False
        self._handle = None

    def draw(self):
        if self._draw_callback is None:
            raise RuntimeError("Объект не связан с рабочей областью проекта.")
        if not self._drawn:
            self._handle = self._draw_callback(self)
            self._drawn = True
        else:
            self.update_draw()
        return self

    def update_draw(self):
        if self._drawn and self._update_callback is not None:
            self._update_callback(self, self._handle)

