from PySide6.QtWidgets import QMessageBox


class ProjectsMixin:
  def refresh_project_list(self):

    self.is_loading_project = True

    self.project_combo.clear()

    projects = self.project_manager.get_all_projects()

    for project in projects:
      self.project_combo.addItem(
          project.name,
          project.id
      )

    if self.current_project_id is not None:

      index = self.project_combo.findData(
          self.current_project_id
      )

      if index >= 0:
        self.project_combo.setCurrentIndex(index)

    self.is_loading_project = False

    self.update_project_title()

  def load_project(self, project_id):

    project = self.project_manager.get_project(project_id)

    if project is None:
      return

    self.is_loading_project = True

    self.current_project_id = project.id
    self.current_project_name = project.name

    self.editor.setPlainText(project.code)

    self.is_dirty = False

    self.settings.set(
        "last_project_id",
        project.id
    )

    index = self.project_combo.findData(project.id)

    if index >= 0:
      self.project_combo.setCurrentIndex(index)

    self.is_loading_project = False

    self.update_project_title()

  def on_project_selected(self, index):

    if self.is_loading_project or index < 0:
      return

    project_id = self.project_combo.itemData(index)

    if project_id is None:
      return

    if project_id == self.current_project_id:
      return

    self.load_project(project_id)

  def on_project_name_edited(self):

    if self.is_loading_project:
      return

    name = self.project_combo.currentText().strip()

    if not name:
      self.update_project_title()
      return

    if name.startswith("* "):
      name = name[2:].strip()

    if not name:
      self.update_project_title()
      return

    if self.current_project_id is None:

      self.current_project_name = name
      self.update_project_title()
      return

    if name == self.current_project_name:
      self.update_project_title()
      return

    try:

      self.project_manager.rename_project(
          self.current_project_id,
          name
      )

      self.current_project_name = name

      self.refresh_project_list()

    except Exception as error:

      QMessageBox.critical(
          self,
          "Ошибка переименования",
          str(error)
      )

      self.update_project_title()

  def on_editor_changed(self):

    if self.is_loading_project:
      return

    self.is_dirty = True

    self.update_project_title()

  def update_project_title(self):

    prefix = "* " if self.is_dirty else ""

    self.project_combo.setEditText(
        prefix + self.current_project_name
    )

  def save_project(self):

    code = self.editor.toPlainText()

    try:

      if self.current_project_id is None:

        project = self.project_manager.create_project(
            self.current_project_name,
            code
        )

        self.current_project_id = project.id

      else:

        self.project_manager.update_project(
            self.current_project_id,
            code
        )

      self.is_dirty = False

      self.settings.set(
          "last_project_id",
          self.current_project_id
      )

      self.refresh_project_list()

      self.status.setText("Проект сохранён")

    except Exception as error:

      QMessageBox.critical(
          self,
          "Ошибка сохранения",
          str(error)
      )

      return

  def delete_current_project(self):
    if self.current_project_id is None:
      QMessageBox.information(
          self,
          "Удаление проекта",
          "Сначала выбери или сохрани проект."
      )
      return

    answer = QMessageBox.question(
        self,
        "Удаление проекта",
        f'Удалить проект «{self.current_project_name}»?',
        QMessageBox.StandardButton.Yes |
        QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )

    if answer != QMessageBox.StandardButton.Yes:
      return

    self.project_manager.delete_project(self.current_project_id)

    self.current_project_id = None
    self.current_project_name = "Новый проект"
    self.is_dirty = False

    self.editor.clear()

    projects = self.project_manager.get_all_projects()

    if projects:
      self.load_project(projects[0].id)
    else:
      self.refresh_project_list()
      self.settings.set("last_project_id", None)

  def create_new_project(self):

    if self.is_dirty:

      answer = QMessageBox.question(
          self,
          "Несохранённые изменения",
          "Текущий проект содержит несохранённые изменения.\n"
          "Создать новый проект без сохранения?",
          QMessageBox.StandardButton.Yes |
          QMessageBox.StandardButton.No,
          QMessageBox.StandardButton.No
      )

      if answer != QMessageBox.StandardButton.Yes:
        return

    try:

      project = self.project_manager.create_project(
          "Новый проект",
          ""
      )

      self.is_loading_project = True

      self.current_project_id = project.id
      self.current_project_name = project.name

      self.editor.clear()

      self.is_dirty = False

      self.settings.set(
          "last_project_id",
          project.id
      )

      self.refresh_project_list()

      self.is_loading_project = False

      self.status.setText("Создан новый проект")

    except Exception as error:

      self.is_loading_project = False

      QMessageBox.critical(
          self,
          "Ошибка создания проекта",
          str(error)
      )
