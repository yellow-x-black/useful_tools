import sys
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from source.common.common import GUITools, PlatformTools
from source.convert_libre_to_pdf.cltp_class import ConvertLibreToPDF
from source.convert_office_to_pdf.cotp_class import ConvertOfficeToPDF
from source.convert_to_md.ctm_class import ConvertToMd
from source.edit_pdf.ep_class import EditPdf
from source.get_file_list.gfl_class import GetFileList
from source.get_japan_government_statistics.gjgs_class import GetJapanGovernmentStatistics


@dataclass
class LauncherItem:
    title: str
    callback: Callable
    description: str | None


class MainApp_Of_Gui_Launcher(QMainWindow):
    def __init__(self):
        """初期化します"""
        super().__init__()
        self.child_windows: list = []
        self._setup_ui()

    def closeEvent(self, event):
        """終了します"""
        super().closeEvent(event)

    def _show_info(self, msg: str) -> None:
        """情報を表示します"""
        QMessageBox.information(self, "情報", msg)

    def _show_result(self, label: str | None, success: bool) -> None:
        """結果を表示します"""
        QMessageBox.information(self, "結果", f"{label} => {'成功' if success else '失敗'}しました。")

    def _show_error(self, msg: str) -> None:
        """エラーを表示します"""
        QMessageBox.warning(self, "エラー", msg)

    def _launch(self, tool: str) -> bool:
        """指定したToolを呼び出します"""
        result: bool = False
        try:
            match tool:
                case "cltp":
                    from source.convert_libre_to_pdf.cltp_with_gui import create_window
                case "cotp":
                    from source.convert_office_to_pdf.cotp_with_gui import create_window
                case "ctm":
                    from source.convert_to_md.ctm_with_gui import create_window
                case "ep":
                    from source.edit_pdf.ep_with_gui import create_window
                case "gfl":
                    from source.get_file_list.gfl_with_gui import create_window
                case "gjgs":
                    from source.get_japan_government_statistics.gjgs_with_gui import create_window
                case _:
                    raise
            window: Any = create_window()
            window.showMaximized()
            self.child_windows.append(window)
        except Exception:
            raise
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
            self.setWindowTitle("Useful Tools - GUI Launcher-")
            central: QWidget = QWidget()
            self.setCentralWidget(central)
            base_layout: QVBoxLayout = QVBoxLayout(central)
            # 主要
            main_scroll_area: QScrollArea = QScrollArea()
            main_scroll_area.setWidgetResizable(True)
            base_layout.addWidget(main_scroll_area)
            main_container: QWidget = QWidget()
            main_container_layout: QVBoxLayout = QVBoxLayout(main_container)
            main_scroll_area.setWidget(main_container)
            main_container_layout.addWidget(QLabel("以下の一覧から選択してください。"))
            # 選択
            launcher_items: list = [
                LauncherItem(
                    title="source/convert_libre_to_pdf",
                    callback=partial(self._launch, "cltp"),
                    description=ConvertLibreToPDF.__doc__,
                ),
                LauncherItem(
                    title="source/convert_office_to_pdf",
                    callback=partial(self._launch, "cotp"),
                    description=ConvertOfficeToPDF.__doc__,
                ),
                LauncherItem(
                    title="source/convert_to_md",
                    callback=partial(self._launch, "ctm"),
                    description=ConvertToMd.__doc__,
                ),
                LauncherItem(
                    title="source/edit_pdf",
                    callback=partial(self._launch, "ep"),
                    description=EditPdf.__doc__,
                ),
                LauncherItem(
                    title="source/get_file_list",
                    callback=partial(self._launch, "gfl"),
                    description=GetFileList.__doc__,
                ),
                LauncherItem(
                    title="source/get_japan_government_statistics",
                    callback=partial(self._launch, "gjgs"),
                    description=GetJapanGovernmentStatistics.__doc__,
                ),
            ]
            for item in launcher_items:
                description: QLabel = QLabel(item.description)
                description.setWordWrap(True)
                btn: QPushButton = QPushButton(item.title)
                btn.clicked.connect(item.callback)
                main_container_layout.addWidget(description)
                main_container_layout.addWidget(btn)
            main_container_layout.addStretch()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result


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
        window: MainApp_Of_Gui_Launcher = MainApp_Of_Gui_Launcher()
        window.resize(1000, 800)
        # 最大化して、表示させる
        window.showMaximized()
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
