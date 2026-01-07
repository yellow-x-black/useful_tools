import sys
from dataclasses import dataclass
from typing import Callable

from PySide6.QtGui import QFont
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

from source.common.common import GUITools
from source.convert_libre_to_pdf.cltp_class import ConvertLibreToPDF
from source.convert_office_to_pdf.cotp_class import ConvertOfficeToPDF
from source.convert_to_md.ctm_class import ConvertToMd
from source.get_file_list.gfl_class import GetFileList
from source.get_government_statistics.g2s_class import GetGovernmentStatistics
from source.pdf_tools.pt_class import PdfTools


@dataclass
class LauncherItem:
    title: str
    callback: Callable
    description: str | None


class MainApp_Of_Gui_Launcher(QMainWindow):
    def __init__(self):
        """初期化します"""
        super().__init__()
        self._setup_ui()

    def closeEvent(self, event):
        """終了します"""
        super().closeEvent(event)

    def _show_info(self, msg: str):
        """情報を表示します"""
        QMessageBox.information(self, "情報", msg)

    def _show_result(self, label: str | None, success: bool):
        """結果を表示します"""
        QMessageBox.information(self, "結果", f"{label} => {'成功' if success else '失敗'}しました。")

    def _show_error(self, msg: str):
        """エラーを表示します"""
        QMessageBox.warning(self, "エラー", msg)

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
                    callback=self.launch_cltp,
                    description=ConvertLibreToPDF.__doc__,
                ),
                LauncherItem(
                    title="source/convert_office_to_pdf",
                    callback=self.launch_cotp,
                    description=ConvertOfficeToPDF.__doc__,
                ),
                LauncherItem(
                    title="source/convert_to_md",
                    callback=self.launch_ctm,
                    description=ConvertToMd.__doc__,
                ),
                LauncherItem(
                    title="source/get_file_list",
                    callback=self.launch_gfl,
                    description=GetFileList.__doc__,
                ),
                LauncherItem(
                    title="source/get_government_statistics",
                    callback=self.launch_g2s,
                    description=GetGovernmentStatistics.__doc__,
                ),
                LauncherItem(
                    title="source/pdf_tools",
                    callback=self.launch_pt,
                    description=PdfTools.__doc__,
                ),
            ]
            for item in launcher_items:
                btn: QPushButton = QPushButton(item.title)
                btn.clicked.connect(item.callback)
                description: QLabel = QLabel(item.description)
                description.setWordWrap(True)
                main_container_layout.addWidget(btn)
                main_container_layout.addWidget(description)
            main_container_layout.addStretch()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    def launch_cltp(self) -> bool:
        """CLTP"""
        result: bool = False
        try:
            from source.convert_libre_to_pdf.cltp_with_gui import MainApp_Of_CLTP, create_window

            self.cltp_window: MainApp_Of_CLTP = create_window()
            self.cltp_window.show()
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def launch_cotp(self) -> bool:
        """COTP"""
        result: bool = False
        try:
            from source.convert_office_to_pdf.cotp_with_gui import MainApp_Of_COTP, create_window

            self.cotp_window: MainApp_Of_COTP = create_window()
            self.cotp_window.show()
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def launch_ctm(self) -> bool:
        """CTM"""
        result: bool = False
        try:
            from source.convert_to_md.ctm_with_gui import MainApp_Of_CTM, create_window

            self.ctm_window: MainApp_Of_CTM = create_window()
            self.ctm_window.show()
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def launch_gfl(self) -> bool:
        """GFL"""
        result: bool = False
        try:
            from source.get_file_list.gfl_with_gui import MainApp_Of_GFL, create_window

            self.gfl_window: MainApp_Of_GFL = create_window()
            self.gfl_window.show()
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def launch_g2s(self) -> bool:
        """G2S"""
        result: bool = False
        try:
            from source.get_government_statistics.g2s_with_gui import MainApp_Of_G2S, create_window

            self.g2s_window: MainApp_Of_G2S = create_window()
            self.g2s_window.show()
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def launch_pt(self) -> bool:
        """PT"""
        result: bool = False
        try:
            from source.pdf_tools.pt_with_gui import MainApp_Of_PT, create_window

            self.pt_window: MainApp_Of_PT = create_window()
            self.pt_window.show()
        except Exception:
            raise
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
        app: QApplication = QApplication(sys.argv)
        # アプリ単位でフォントを設定する
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
