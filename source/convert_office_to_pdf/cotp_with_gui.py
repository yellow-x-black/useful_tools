import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from source.common.common import DatetimeTools, GUITools, LogTools


class LogEmitter(QObject):
    """loggingの出力をQtのSignalに変換し、GUIスレッドへ安全にログを伝達するためのクラス"""

    log_signal: Signal = Signal(str)


class QTextEditHandler(logging.Handler):
    """QTextEditにログを流すためのハンドラ"""

    def __init__(self, emitter: LogEmitter):
        super().__init__()
        self.emitter: LogEmitter = emitter

    def emit(self, record: logging.LogRecord):
        msg: str = self.format(record)
        self.emitter.log_signal.emit(msg)


class MainApp_Of_COTP(QMainWindow):
    def __init__(self, obj_of_cls: Any):
        """初期化します"""
        super().__init__()
        self.obj_of_lt: LogTools = LogTools()
        self.obj_of_cls: Any = obj_of_cls(self.obj_of_lt.logger)
        self._setup_ui()
        self.obj_of_dt2: DatetimeTools = DatetimeTools()
        self._setup_log()

    def closeEvent(self, event):
        """終了します"""
        if self.obj_of_lt:
            self._show_info(f"ログファイルは、\n{self.obj_of_lt.file_path_of_log}\nに出力されました。")
        for h in self.obj_of_lt.logger.handlers[:]:
            if isinstance(h, QTextEditHandler):
                self.obj_of_lt.logger.removeHandler(h)
        super().closeEvent(event)

    def _show_info(self, msg: str):
        """情報を表示します"""
        QMessageBox.information(self, "情報", msg)
        self.obj_of_lt.logger.info(msg)

    def _show_result(self, label: str | None, success: bool):
        """結果を表示します"""
        QMessageBox.information(self, "結果", f"{label} => {'成功' if success else '失敗'}しました。")
        if success:
            self.obj_of_lt.logger.info(f"{label} => 成功しました。")
        else:
            self.obj_of_lt.logger.error(f"{label} => 失敗しました。")

    def _show_error(self, msg: str):
        """エラーを表示します"""
        QMessageBox.warning(self, "エラー", msg)
        self.obj_of_lt.logger.warning(msg)

    def _setup_log(self) -> bool:
        """ログを設定します"""
        result: bool = False
        try:
            # exe化されている場合とそれ以外を切り分ける
            exe_path: Path = Path(sys.executable) if getattr(sys, "frozen", False) else Path(__file__)
            # ログフォルダのパス
            folder_p: Path = exe_path.parent / "__log__"
            # ログフォルダが存在しない場合は、作成します
            folder_p.mkdir(parents=True, exist_ok=True)
            # ログファイル名
            file_name: str = f"log_{self.obj_of_dt2._convert_for_file_name()}.log"
            file_p: Path = folder_p / file_name
            self.obj_of_lt.file_path_of_log = str(file_p)
            self.obj_of_lt._setup_file_handler(self.obj_of_lt.file_path_of_log)
            self.log_emitter: LogEmitter = LogEmitter()
            self.log_emitter.log_signal.connect(self.log_area.append)
            text_handler: QTextEditHandler = QTextEditHandler(self.log_emitter)
            text_handler.setFormatter(self.obj_of_lt.file_formatter)
            self.obj_of_lt.logger.addHandler(text_handler)
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    def _setup_ui(self) -> bool:
        """User Interfaceを設定します"""
        result: bool = False
        try:
            # タイトル
            self.setWindowTitle("Officeファイル => PDF 一括変換アプリ with Microsoft Office")
            central: QWidget = QWidget()
            self.setCentralWidget(central)
            base_layout: QVBoxLayout = QVBoxLayout(central)
            # 主要
            main_scroll_area: QScrollArea = QScrollArea()
            main_scroll_area.setWidgetResizable(True)
            base_layout.addWidget(main_scroll_area)
            main_container: QWidget = QWidget()
            main_container_layout: QFormLayout = QFormLayout(main_container)
            main_scroll_area.setWidget(main_container)
            # 概要
            overview_area: QTextEdit = QTextEdit()
            overview_area.setReadOnly(True)
            lines_of_overview: list = []
            lines_of_overview.append("以下が変換元に指定できるファイルの拡張子の一覧です。\n")
            for key, info in self.obj_of_cls.file_types.items():
                values: str = ""
                for value in info:
                    values += f"{value}, "
                values = values.rstrip(", ")
                lines_of_overview.append(f"{key}: {values}")
            overview_area.setText("\n".join(lines_of_overview))
            main_container_layout.addRow(QLabel("概要: "))
            main_container_layout.addRow(overview_area)
            # 変換元
            label_from: QLabel = QLabel("変換元のフォルダ: 未選択")
            main_container_layout.addRow(label_from)
            btn_select_from: QPushButton = QPushButton("変換元のフォルダを選択する")
            main_container_layout.addRow(btn_select_from)
            btn_select_from.clicked.connect(lambda *args, lbl=label_from: self.select_folder_from(lbl))
            btn_open_from: QPushButton = QPushButton("変換元のフォルダを開く")
            main_container_layout.addRow(btn_open_from)
            btn_open_from.clicked.connect(lambda *args: self.open_explorer(self.obj_of_cls.folder_path_from))
            # 対象ファイルの一覧
            main_container_layout.addRow(QLabel("変換対象ファイルの一覧: "))
            self.lst_widget: QListWidget = QListWidget()
            main_container_layout.addRow(self.lst_widget)
            # 変換先
            label_to: QLabel = QLabel("変換先のフォルダ: 未選択")
            main_container_layout.addRow(label_to)
            btn_select_to: QPushButton = QPushButton("変換先のフォルダを選択する")
            main_container_layout.addRow(btn_select_to)
            btn_select_to.clicked.connect(lambda *args, lbl=label_to: self.select_folder_to(lbl))
            btn_open_to: QPushButton = QPushButton("変換先のフォルダを開く")
            main_container_layout.addRow(btn_open_to)
            btn_open_to.clicked.connect(lambda *args: self.open_explorer(self.obj_of_cls.folder_path_to))
            # 進行状況
            main_container_layout.addRow(QLabel("進行状況: "))
            self.progress_bar: QProgressBar = QProgressBar()
            main_container_layout.addRow(self.progress_bar)
            # 実行
            btn_convert: QPushButton = QPushButton("PDFファイルへの一括変換を実行する")
            main_container_layout.addRow(btn_convert)
            btn_convert.clicked.connect(self.convert_all_files)
            # ログ
            self.log_area: QTextEdit = QTextEdit()
            self.log_area.setReadOnly(True)
            main_container_layout.addRow(QLabel("ログ: "))
            main_container_layout.addRow(self.log_area)
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    def select_folder_from(self, lbl: QLabel) -> bool:
        """変換元のフォルダを選択します"""
        result: bool = False
        try:
            self.obj_of_cls.folder_path_from = QFileDialog.getExistingDirectory(self, caption="変換元のフォルダを選択")
            folder_p: Path = Path(self.obj_of_cls.folder_path_from).expanduser()
            self.obj_of_cls.folder_path_from = str(folder_p)
            if self.obj_of_cls.folder_path_from:
                lbl.setText(f"変換元フォルダ: {self.obj_of_cls.folder_path_from}")
                if self.obj_of_cls.folder_path_to:
                    self.show_file_lst()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    def select_folder_to(self, lbl: QLabel) -> bool:
        """変換先のフォルダを選択します"""
        result: bool = False
        try:
            self.obj_of_cls.folder_path_to = QFileDialog.getExistingDirectory(self, caption="変換先のフォルダを選択")
            folder_p: Path = Path(self.obj_of_cls.folder_path_to).expanduser()
            self.obj_of_cls.folder_path_to = str(folder_p)
            if self.obj_of_cls.folder_path_to:
                lbl.setText(f"変換先フォルダ: {self.obj_of_cls.folder_path_to}")
                if self.obj_of_cls.folder_path_from:
                    self.show_file_lst()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    def open_explorer(self, folder_path: str) -> bool:
        """エクスプローラーを開きます"""
        result: bool = False
        try:
            if folder_path == "":
                raise Exception("フォルダを選択してください。")
            subprocess.run(["explorer", folder_path], shell=False)
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    def show_file_lst(self) -> bool:
        """ファイル一覧を表示します"""
        result: bool = False
        try:
            self.obj_of_cls.create_file_lst()
            self.lst_widget.clear()
            for f in self.obj_of_cls.filtered_lst_of_f:
                file_p: Path = Path(f)
                file_s: str = file_p.name
                self.lst_widget.addItem(file_s)
            self.progress_bar.setValue(0)
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    def convert_all_files(self) -> bool:
        """全てのファイルを一括変換します"""
        result: bool = False
        try:
            if not self.obj_of_cls.filtered_lst_of_f:
                raise Exception("ファイルリストが初期化されていません。")
            self.progress_bar.setRange(0, self.obj_of_cls.number_of_f)
            for i in range(self.obj_of_cls.number_of_f):
                self.obj_of_cls.handle_file()
                self.progress_bar.setValue(i + 1)
                if self.obj_of_cls.complete:
                    break
                self.obj_of_cls.move_to_next_file()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            self._show_result(self.convert_all_files.__doc__, result)
        return result


def create_window() -> MainApp_Of_COTP:
    # エラーチェック
    from source.convert_office_to_pdf.cotp_class import ConvertOfficeToPDF

    window: MainApp_Of_COTP = MainApp_Of_COTP(ConvertOfficeToPDF)

    window.resize(1000, 800)
    # 最大化して、表示させる
    window.showMaximized()
    return window


def main() -> bool:
    """主要関数"""
    result: bool = False
    try:
        obj_of_gt: GUITools = GUITools()
        app: QApplication = QApplication(sys.argv)
        # アプリ単位でフォントを設定する
        font: QFont = QFont()
        font.setPointSize(12)
        app.setFont(font)
        create_window()
        sys.exit(app.exec())
    except ImportError as e:
        obj_of_gt._show_start_up_error(f"error: \n{str(e)}")
    except Exception as e:
        obj_of_gt._show_start_up_error(f"error: \n{str(e)}")
    else:
        result = True
    finally:
        pass
    return result


if __name__ == "__main__":
    main()
