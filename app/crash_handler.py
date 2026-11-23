import faulthandler
import logging
import os
import sys
import threading
import traceback
from pathlib import Path

from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from PySide6.QtWidgets import QApplication, QMessageBox


APP_NAME = "Geometry Playground 2.0"
LOG_DIR = Path(
    os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
) / "ZifTech" / "Geometry Playground 2.0"
LOG_FILE = LOG_DIR / "crash.log"

_logger = logging.getLogger("geometry_playground")
_logger.setLevel(logging.DEBUG)
_logger.propagate = False

_log_handle = None
_last_context = "Запуск приложения"
_dialog_active = False


def set_crash_context(context):
    global _last_context
    _last_context = str(context)
    if _logger.handlers:
        _logger.info("ЭТАП: %s", _last_context)


def _format_exception(exc_info):
    return "".join(traceback.format_exception(*exc_info))


def _write_exception(context, exc_info):
    details = _format_exception(exc_info)
    _logger.critical(
        "НЕОБРАБОТАННОЕ ИСКЛЮЧЕНИЕ\nЭтап: %s\n%s",
        context,
        details
    )
    for handler in _logger.handlers:
        handler.flush()
    return details


def report_exception(context, exc_info=None, show_dialog=True):
    if exc_info is None:
        exc_info = sys.exc_info()

    details = _write_exception(context, exc_info)
    if show_dialog:
        _show_error_dialog(
            f"Произошла ошибка на этапе: {context}",
            details
        )


def _show_error_dialog(summary, details):
    global _dialog_active

    if _dialog_active:
        return

    app = QApplication.instance()
    if app is None:
        return

    _dialog_active = True
    try:
        message = (
            f"{summary}\n\n"
            f"Подробности записаны в файл:\n{LOG_FILE}\n\n"
            f"{details[-9000:]}"
        )
        QMessageBox.critical(None, "Ошибка Geometry Playground", message)
    except Exception:
        _logger.exception("Не удалось показать диалог ошибки")
    finally:
        _dialog_active = False


def _sys_exception_hook(exc_type, exc_value, exc_traceback):
    exc_info = (exc_type, exc_value, exc_traceback)
    details = _write_exception(_last_context, exc_info)
    _show_error_dialog(
        f"Необработанная ошибка. Последний этап: {_last_context}",
        details
    )


def _thread_exception_hook(args):
    exc_info = (args.exc_type, args.exc_value, args.exc_traceback)
    _write_exception(
        f"Поток {args.thread.name if args.thread else 'unknown'}",
        exc_info
    )


def _qt_message_handler(mode, context, message):
    level = {
        QtMsgType.QtDebugMsg: logging.DEBUG,
        QtMsgType.QtInfoMsg: logging.INFO,
        QtMsgType.QtWarningMsg: logging.WARNING,
        QtMsgType.QtCriticalMsg: logging.ERROR,
        QtMsgType.QtFatalMsg: logging.CRITICAL
    }.get(mode, logging.ERROR)

    location = ""
    if context is not None:
        location = (
            f" [{context.file or '?'}:{context.line}]"
        )

    _logger.log(level, "Qt%s: %s%s", " fatal" if mode == QtMsgType.QtFatalMsg else "", message, location)

    if mode == QtMsgType.QtFatalMsg:
        _logger.critical("Последний этап приложения: %s", _last_context)
        for handler in _logger.handlers:
            handler.flush()


def install_crash_handler():
    global _log_handle

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if not _logger.handlers:
        file_handler = logging.FileHandler(
            LOG_FILE,
            mode="a",
            encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        _logger.addHandler(file_handler)

    _log_handle = open(LOG_FILE, "a", encoding="utf-8")
    faulthandler.enable(file=_log_handle, all_threads=True)

    sys.excepthook = _sys_exception_hook
    if hasattr(threading, "excepthook"):
        threading.excepthook = _thread_exception_hook

    qInstallMessageHandler(_qt_message_handler)

    _logger.info("\n%s", "=" * 72)
    _logger.info("Запуск %s", APP_NAME)
    set_crash_context("Инициализация системы диагностики")
    _logger.info("Журнал ошибок: %s", LOG_FILE)

    return LOG_FILE
