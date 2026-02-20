import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QFontDatabase
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

from source.common.common import DatetimeTools, GUITools, LogTools, PlatformTools


class MainApp_Of_CLTP(QMainWindow):
    """GUIアプリ"""

    log: Signal = Signal(str)

    def __init__(self, obj_of_cls: Any):
        """初期化します"""
        super().__init__()
        self.obj_of_lt: LogTools = LogTools()
        self.obj_of_dt2: DatetimeTools = DatetimeTools()
        self.obj_of_pft: PlatformTools = PlatformTools()
        self.obj_of_cls: Any = obj_of_cls(self.obj_of_lt.logger)
        self._setup_ui()
        self._setup_log()

    def closeEvent(self, event):
        """終了します"""
        if self.obj_of_lt:
            self._show_info(f"ログファイルは、\n{self.obj_of_lt.file_path_of_log}\nに出力されました。")
        super().closeEvent(event)

    def _show_info(self, msg: str) -> None:
        """情報を表示します"""
        QMessageBox.information(self, "情報", msg)
        self.obj_of_lt.logger.info(msg)

    def _show_result(self, label: str | None, success: bool) -> None:
        """結果を表示します"""
        QMessageBox.information(self, "結果", f"{label} => {'成功' if success else '失敗'}しました。")
        if success:
            self.obj_of_lt.logger.info(f"{label} => 成功しました。")
        else:
            self.obj_of_lt.logger.error(f"{label} => 失敗しました。")

    def _show_error(self, msg: str) -> None:
        """エラーを表示します"""
        QMessageBox.warning(self, "エラー", msg)
        self.obj_of_lt.logger.warning(msg)

    @Slot(str)
    def _append_log(self, msg: str) -> None:
        """ログを追加します"""
        self.log_area.append(msg)

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
            self.obj_of_lt._setup_qt_signal_handler(self.log)
            self.log.connect(self._append_log, Qt.ConnectionType.QueuedConnection)
            self.obj_of_lt.logger.propagate = False
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
            self.obj_of_cls.append_init_log()
        finally:
            pass
        return result

    def _setup_ui(self) -> bool:
        """User Interfaceを設定します"""
        result: bool = False
        try:
            # タイトル
            self.setWindowTitle("Officeファイル => PDFファイル 一括変換アプリ with LibreOffice")
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
            self.label_from: QLabel = QLabel("変換元のフォルダ: 未選択")
            main_container_layout.addRow(self.label_from)
            btn_select_from: QPushButton = QPushButton("変換元のフォルダを選択する")
            main_container_layout.addRow(btn_select_from)
            btn_select_from.clicked.connect(self.select_folder_from)
            btn_open_from: QPushButton = QPushButton("変換元のフォルダを開く")
            main_container_layout.addRow(btn_open_from)
            btn_open_from.clicked.connect(self.open_explorer_on_folder_from)
            # 対象ファイルの一覧
            main_container_layout.addRow(QLabel("変換対象ファイルの一覧: "))
            self.lst_widget: QListWidget = QListWidget()
            main_container_layout.addRow(self.lst_widget)
            # 変換先
            self.label_to: QLabel = QLabel("変換先のフォルダ: 未選択")
            main_container_layout.addRow(self.label_to)
            btn_select_to: QPushButton = QPushButton("変換先のフォルダを選択する")
            main_container_layout.addRow(btn_select_to)
            btn_select_to.clicked.connect(self.select_folder_to)
            btn_open_to: QPushButton = QPushButton("変換先のフォルダを開く")
            main_container_layout.addRow(btn_open_to)
            btn_open_to.clicked.connect(self.open_explorer_on_folder_to)
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

    @Slot()
    def select_folder_from(self) -> bool:
        """変換元のフォルダを選択します"""
        result: bool = False
        try:
            self.obj_of_cls.folder_path_from = QFileDialog.getExistingDirectory(self, caption="変換元のフォルダを選択")
            folder_p: Path = Path(self.obj_of_cls.folder_path_from).expanduser()
            self.obj_of_cls.folder_path_from = str(folder_p)
            if self.obj_of_cls.folder_path_from:
                self.label_from.setText(f"変換元フォルダ: {self.obj_of_cls.folder_path_from}")
                if self.obj_of_cls.folder_path_to:
                    self.show_file_lst()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    @Slot()
    def select_folder_to(self) -> bool:
        """変換先のフォルダを選択します"""
        result: bool = False
        try:
            self.obj_of_cls.folder_path_to = QFileDialog.getExistingDirectory(self, caption="変換先のフォルダを選択")
            folder_p: Path = Path(self.obj_of_cls.folder_path_to).expanduser()
            self.obj_of_cls.folder_path_to = str(folder_p)
            if self.obj_of_cls.folder_path_to:
                self.label_to.setText(f"変換先フォルダ: {self.obj_of_cls.folder_path_to}")
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
        EXPLORER_OF_WSL: str = "/mnt/c/Windows/explorer.exe"
        try:
            if folder_path == "":
                raise Exception("フォルダを選択してください。")
            if platform.system().lower() == "windows":
                subprocess.run(["explorer", folder_path], shell=False)
            elif self.obj_of_pft._is_wsl():
                # Windowsのパスに変換（/mnt/c/... 形式）
                wsl_path: str = subprocess.check_output(["wslpath", "-w", folder_path]).decode("utf-8").strip()
                subprocess.run([EXPLORER_OF_WSL, wsl_path])
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    @Slot()
    def open_explorer_on_folder_from(self) -> None:
        """変換元のフォルダでエクスプローラーを開きます"""
        self.open_explorer(self.obj_of_cls.folder_path_from)

    @Slot()
    def open_explorer_on_folder_to(self) -> None:
        """変換先のフォルダでエクスプローラーを開きます"""
        self.open_explorer(self.obj_of_cls.folder_path_to)

    @Slot()
    def convert_all_files(self) -> bool:
        """全てのファイルを一括変換します"""
        result: bool = False
        try:
            if not self.obj_of_cls.filtered_lst_of_f:
                raise Exception("ファイルリストが初期化されていません。")
            self.progress_bar.setRange(0, self.obj_of_cls.number_of_f)
            for i in range(self.obj_of_cls.number_of_f):
                self.obj_of_cls.convert_file()
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


def create_window() -> MainApp_Of_CLTP:
    # エラーチェック
    from source.convert_libre_to_pdf.cltp_class import ConvertLibreToPDF

    window: MainApp_Of_CLTP = MainApp_Of_CLTP(ConvertLibreToPDF)
    return window


def main() -> bool:
    """主要関数"""
    result: bool = False
    try:
        obj_of_gt: GUITools = GUITools()
        obj_of_pft: PlatformTools = PlatformTools()
        app: QApplication = QApplication(sys.argv)
        # アプリ単位でフォントを設定する
        if obj_of_pft._is_wsl():
            font_path: str = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
            font_id: int = QFontDatabase.addApplicationFont(font_path)
            font_family: str = QFontDatabase.applicationFontFamilies(font_id)[0]
            font: QFont = QFont(font_family)
        else:
            font: QFont = QFont()
        font.setPointSize(12)
        app.setFont(font)
        window: MainApp_Of_CLTP = create_window()
        window.resize(1000, 800)
        # 最大化して、表示させる
        window.showMaximized()
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
