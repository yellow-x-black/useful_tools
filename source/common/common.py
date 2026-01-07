import datetime
import logging
import platform
import sys
from logging import FileHandler, Formatter, Logger, StreamHandler
from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox, QWidget


class LogTools:
    """
    * logger.debug(): デバッグ
    * logger.info(): 通常
    * logger.warning(): 小さいエラー
    * logger.error(): 普通のエラー
    * logger.critical(): 大きいエラー
    """

    def __init__(self):
        """初期化します"""
        self.file_path_of_log: str = ""
        # create logger
        self.logger: Logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def _setup_file_handler(self, file_path: str) -> bool:
        """FileHandlerを設定します"""
        result: bool = False
        try:
            self.file_handler: FileHandler = logging.FileHandler(file_path, mode="w", encoding="utf-8")
            self.file_handler.setLevel(logging.INFO)
            self.STR_OF_FILE_FORMATTER: str = "%(message)s - [%(levelname)s] - (%(filename)s) - %(asctime)s"
            self.file_formatter: Formatter = logging.Formatter(self.STR_OF_FILE_FORMATTER)
            self.file_handler.setFormatter(self.file_formatter)
            self.logger.addHandler(self.file_handler)
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def _setup_stream_handler(self) -> bool:
        """StreamHandlerを設定します"""
        result: bool = False
        try:
            self.stream_handler: StreamHandler = logging.StreamHandler(sys.stdout)
            self.stream_handler.setLevel(logging.INFO)
            self.STR_OF_STREAM_FORMATTER: str = "%(message)s"
            self.stream_formatter: Formatter = logging.Formatter(self.STR_OF_STREAM_FORMATTER)
            self.stream_handler.setFormatter(self.stream_formatter)
            self.logger.addHandler(self.stream_handler)
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result


class PlatformTools:
    def __init__(self):
        """初期化します"""
        pass

    def _is_wsl(self) -> bool:
        """WSL環境かどうか判定します"""
        result: bool = False
        try:
            if platform.system().lower() == "linux":
                with open("/proc/version", "r") as f:
                    content: str = f.read().lower()
                    if "microsoft" in content or "wsl" in content:
                        result = True
        except Exception:
            raise
        else:
            pass
        finally:
            pass
        return result


class DatetimeTools:
    def __init__(self):
        """初期化します"""
        self.dt: Any = None

    def _convert_dt_to_str(self, dt: Any = None) -> str:
        """datetime型からstr型に変換します"""
        if dt is None:
            self.dt = datetime.datetime.now()
            dt = self.dt
        # datetime型 => str型
        return dt.strftime("%Y-%m-%d_%H:%M:%S")

    def _convert_for_file_name(self, dt: Any = None) -> str:
        """ファイル名用に変換します"""
        if dt is None:
            self.dt = datetime.datetime.now()
            dt = self.dt
        # datetime型 => str型
        return dt.strftime("%Y%m%d_%H%M%S")

    def _convert_for_metadata_in_pdf(self, utc: str, dt: Any = None) -> str:
        """pdfのメタデータ用に変換します"""
        if dt is None:
            self.dt = datetime.datetime.now()
            dt = self.dt
        # datetime型 => str型
        return dt.strftime(f"D\072%Y%m%d%H%M%S{utc}")


class GUITools:
    def __init__(self, parent: QWidget | None = None):
        """初期化します"""
        self.parent: QWidget | None = parent

    def _show_start_up_error(self, msg: str):
        """起動エラーのウィンドウを表示します"""
        box: QMessageBox = QMessageBox(self.parent)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle("エラー")
        box.setText(msg)
        box.setStyleSheet("""
            QMessageBox { font-size: 12pt; }
        """)
        # 一定時間後に自動終了する
        MILLI_SECONDS: int = 10000
        QTimer.singleShot(MILLI_SECONDS, box.accept)
        box.exec()
