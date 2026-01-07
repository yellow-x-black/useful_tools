import logging
import platform
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from source.common.common import DatetimeTools, GUITools, LogTools, PlatformTools
from source.get_file_list.gfl_class import GetFileList


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


class MainApp_Of_GFL(QMainWindow):
    def __init__(self):
        """初期化します"""
        super().__init__()
        self.obj_of_lt: LogTools = LogTools()
        self.obj_of_cls: GetFileList = GetFileList(self.obj_of_lt.logger)
        self._setup_ui()
        self.obj_of_dt2: DatetimeTools = DatetimeTools()
        self.obj_of_pft: PlatformTools = PlatformTools()
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
            self.setWindowTitle("ファイル検索アプリ")
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
            # フォルダ
            folder_label: QLabel = QLabel("フォルダ: 未選択")
            main_container_layout.addRow(folder_label)
            select_folder_btn: QPushButton = QPushButton("フォルダを選択する")
            main_container_layout.addRow(select_folder_btn)
            select_folder_btn.clicked.connect(lambda *args, lbl=folder_label: self.select_folder(lbl))
            open_folder_btn: QPushButton = QPushButton("フォルダを開く")
            main_container_layout.addRow(open_folder_btn)
            open_folder_btn.clicked.connect(self.open_explorer)
            # 再帰的
            recursive_checkbox: QCheckBox = QCheckBox("サブフォルダも含めて検索する（再帰的）")
            main_container_layout.addRow(recursive_checkbox)
            recursive_checkbox.toggled.connect(lambda *args, chckbx=recursive_checkbox: self._get_recursive(chckbx))
            # 検索パターン
            main_container_layout.addRow(QLabel("検索パターン:"))
            pattern_input: QLineEdit = QLineEdit()
            pattern_input.setPlaceholderText("検索パターンを入力...")
            pattern_input.editingFinished.connect(lambda *args, lndt=pattern_input: self._get_pattern(lndt))
            main_container_layout.addRow(pattern_input)
            # 実行
            search_btn: QPushButton = QPushButton("検索パターンで検索する")
            main_container_layout.addRow(search_btn)
            search_btn.clicked.connect(self.search_files)
            # ログ
            self.log_area: QTextEdit = QTextEdit()
            self.log_area.setReadOnly(True)
            main_container_layout.addRow(QLabel("ログ:"))
            main_container_layout.addRow(self.log_area)
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    def _get_recursive(self, chckbx: QCheckBox):
        """再帰的かどうかを取得します"""
        try:
            self.obj_of_cls.recursive = chckbx.isChecked()
            self.obj_of_cls.search_directly_under_folder()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            pass
        finally:
            pass

    def _get_pattern(self, lndt: QLineEdit):
        """検索パターンを取得します"""
        try:
            self.obj_of_cls.pattern = lndt.text().strip()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            pass
        finally:
            pass

    def select_folder(self, lbl: QLabel) -> bool:
        """フォルダを選択します"""
        result: bool = False
        try:
            self.obj_of_cls.folder_path = QFileDialog.getExistingDirectory(self, caption="フォルダを選択")
            folder_p: Path = Path(self.obj_of_cls.folder_path).expanduser()
            self.obj_of_cls.folder_path = str(folder_p)
            lbl.setText(self.obj_of_cls.folder_path)
            self.obj_of_cls.search_directly_under_folder()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    def open_explorer(self) -> bool:
        """エクスプローラーを開きます"""
        result: bool = False
        EXPLORER_OF_WSL: str = "/mnt/c/Windows/explorer.exe"
        try:
            if self.obj_of_cls.folder_path == "":
                raise Exception("フォルダを選択してください。")
            if platform.system().lower() == "windows":
                subprocess.run(["explorer", self.obj_of_cls.folder_path], shell=False)
            elif self.obj_of_pft._is_wsl():
                # Windowsのパスに変換（/mnt/c/... 形式）
                wsl_path: str = subprocess.check_output(["wslpath", "-w", self.obj_of_cls.folder_path]).decode("utf-8").strip()
                subprocess.run([EXPLORER_OF_WSL, wsl_path])
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    def search_files(self) -> bool:
        """ファイルを検索します"""
        result: bool = False
        try:
            if self.obj_of_cls.folder_path == "":
                raise Exception("フォルダを選択してください。")
            if self.obj_of_cls.pattern == "":
                raise Exception("検索パターンを入力してください。")
            self.obj_of_cls.extract_by_pattern()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            self._show_result(self.search_files.__doc__, result)
        return result


def create_window() -> MainApp_Of_GFL:
    window: MainApp_Of_GFL = MainApp_Of_GFL()
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
    except Exception as e:
        obj_of_gt._show_start_up_error(f"error: \n{str(e)}")
    else:
        result = True
    finally:
        pass
    return result


if __name__ == "__main__":
    main()
