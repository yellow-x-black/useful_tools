import asyncio
import re
import sys
from logging import Logger
from pathlib import Path
from threading import Event

import httpx
import pandas as pd
from pandas.io.parsers import TextFileReader
from PySide6.QtCore import QModelIndex, QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QFontDatabase, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLayoutItem,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from source.common.common import DatetimeTools, GUITools, LogTools, PlatformTools
from source.get_japan_government_statistics.gjgs_class import GetJapanGovernmentStatistics


class GetIdsWorker(QObject):
    """統計表IDの一覧を取得する処理の非同期ワーカー"""

    finished: Signal = Signal(bool)
    error: Signal = Signal(str)
    log: Signal = Signal(str)

    def __init__(self, logger: Logger, APP_ID: str, lst_of_data_type: list, lst_of_get_type: list):
        """初期化します"""
        super().__init__()
        self.cancel_event: Event = Event()
        # 共有する
        self.logger: Logger = logger
        self.obj_of_cls: GetJapanGovernmentStatistics = GetJapanGovernmentStatistics(self.logger, self.cancel_event)
        self.obj_of_cls.APP_ID = APP_ID
        self.obj_of_cls.lst_of_data_type = lst_of_data_type
        self.obj_of_cls.lst_of_get_type = lst_of_get_type

    def run(self) -> None:
        """実行します"""
        result: bool = False
        loop: asyncio.AbstractEventLoop | None = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.obj_of_cls.write_stats_data_ids_to_file())
        except asyncio.CancelledError:
            result = False
        except httpx.HTTPStatusError as e:
            self.logger.error(str(e))
            self.error.emit(str(e))
        except httpx.RequestError as e:
            self.logger.error(str(e))
            self.error.emit(str(e))
        except Exception as e:
            self.logger.error(str(e))
            self.error.emit(str(e))
        else:
            pass
        finally:
            if loop is not None:
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
        if result:
            self.logger.info("統計表IDの取得が完了しました。")
        else:
            self.logger.warning("統計表IDの取得がキャンセルされました。")
        self.finished.emit(result)

    def cancel(self) -> None:
        """キャンセルします"""
        self.cancel_event.set()


class MainApp_Of_GJGS(QMainWindow):
    """GUIアプリ"""

    log: Signal = Signal(str)

    def __init__(self):
        """初期化します"""
        super().__init__()
        self.obj_of_lt: LogTools = LogTools()
        self.obj_of_dt2: DatetimeTools = DatetimeTools()
        self.obj_of_cls: GetJapanGovernmentStatistics = GetJapanGovernmentStatistics(self.obj_of_lt.logger)
        self._setup_first_ui()
        self._setup_log()
        self.worker_of_getting_ids: GetIdsWorker | None = None
        self.thread_of_getting_ids: QThread | None = None

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

    def _setup_first_ui(self) -> bool:
        """1番目のUser Interfaceを設定します"""
        result: bool = False
        try:
            # タイトル
            self.setWindowTitle("日本政府統計表示アプリ")
            central: QWidget = QWidget()
            self.setCentralWidget(central)
            # 主要
            self.main_layout: QVBoxLayout = QVBoxLayout(central)
            # 上
            self.top_layout: QHBoxLayout = QHBoxLayout()
            self.main_layout.addLayout(self.top_layout, stretch=2)
            # 左上(統計表ID)
            self.top_left_grp_bx: QGroupBox = QGroupBox(title="統計表ID")
            self.layout_of_top_left: QVBoxLayout = QVBoxLayout(self.top_left_grp_bx)
            self.top_left_scroll_area: QScrollArea = QScrollArea()
            self.top_left_scroll_area.setWidgetResizable(True)
            self.layout_of_top_left.addWidget(self.top_left_scroll_area)
            self.top_layout.addWidget(self.top_left_grp_bx, stretch=1)
            self._setup_second_ui()
            # 右上(ログ)
            self.top_right_grp_bx: QGroupBox = QGroupBox(title="ログ")
            self.layout_of_top_right: QVBoxLayout = QVBoxLayout(self.top_right_grp_bx)
            self.top_right_scroll_area: QScrollArea = QScrollArea()
            self.top_right_scroll_area.setWidgetResizable(True)
            self.top_right_container: QWidget = QWidget()
            self.top_right_container_layout: QVBoxLayout = QVBoxLayout(self.top_right_container)
            self.log_area: QTextEdit = QTextEdit()
            self.log_area.setReadOnly(True)
            self.top_right_container_layout.addWidget(self.log_area)
            self.top_right_scroll_area.setWidget(self.top_right_container)
            self.layout_of_top_right.addWidget(self.top_right_scroll_area)
            self.top_layout.addWidget(self.top_right_grp_bx, stretch=1)
            # 下
            self.bottom_layout: QHBoxLayout = QHBoxLayout()
            self.main_layout.addLayout(self.bottom_layout, stretch=2)
            # 左下(統計表)
            self.bottom_left_grp_bx: QGroupBox = QGroupBox(title="統計表")
            self.layout_of_bottom_left: QVBoxLayout = QVBoxLayout(self.bottom_left_grp_bx)
            self.bottom_left_scroll_area: QScrollArea = QScrollArea()
            self.bottom_left_scroll_area.setWidgetResizable(True)
            self.layout_of_bottom_left.addWidget(self.bottom_left_scroll_area)
            self.bottom_layout.addWidget(self.bottom_left_grp_bx, stretch=1)
            # 右下(機能)
            self.bottom_right_grp_bx: QGroupBox = QGroupBox(title="機能")
            self.layout_of_bottom_right: QVBoxLayout = QVBoxLayout(self.bottom_right_grp_bx)
            self.bottom_right_scroll_area: QScrollArea = QScrollArea()
            self.bottom_right_scroll_area.setWidgetResizable(True)
            self.bottom_right_container: QWidget = QWidget()
            self.bottom_right_container_layout: QVBoxLayout = QVBoxLayout(self.bottom_right_container)
            self.bottom_right_form: QFormLayout = QFormLayout()
            self.bottom_right_container_layout.addLayout(self.bottom_right_form)
            self.bottom_right_scroll_area.setWidget(self.bottom_right_container)
            self.layout_of_bottom_right.addWidget(self.bottom_right_scroll_area)
            self.bottom_layout.addWidget(self.bottom_right_grp_bx, stretch=1)
            # アプリケーションID
            self.app_id_text: QLineEdit = QLineEdit()
            self.app_id_text.editingFinished.connect(self._get_app_id)
            self.bottom_right_form.addRow(QLabel("アプリケーションID: "), self.app_id_text)
            # データタイプ
            self.data_type_combo: QComboBox = QComboBox()
            for key, desc in self.obj_of_cls.dct_of_data_type.items():
                self.data_type_combo.addItem(f"{key}: {desc}", userData=key)
            self.data_type_combo.currentIndexChanged.connect(self._get_data_type)
            self._get_data_type(0)
            self.bottom_right_form.addRow(QLabel("データタイプ: "), self.data_type_combo)
            # 取得方法
            self.get_type_combo: QComboBox = QComboBox()
            for key, desc in self.obj_of_cls.dct_of_get_type.items():
                self.get_type_combo.addItem(f"{key}: {desc}", userData=key)
            self.get_type_combo.currentIndexChanged.connect(self._get_get_type)
            self._get_get_type(0)
            self.bottom_right_form.addRow(QLabel("取得方法: "), self.get_type_combo)
            # 統計表IDの一覧を取得する
            self.get_ids_btn: QPushButton = QPushButton("統計表IDの一覧を取得する")
            self.get_ids_btn.clicked.connect(self.get_lst_of_ids)
            # 統計表IDの一覧の取得をキャンセルする
            self.cancel_getting_ids_btn: QPushButton = QPushButton("統計表IDの一覧の取得をキャンセルする")
            self.cancel_getting_ids_btn.clicked.connect(self.cancel_getting_lst_of_ids)
            self.bottom_right_form.addRow(self.get_ids_btn, self.cancel_getting_ids_btn)
            # 統計表IDの一覧を表示する
            show_ids_btn: QPushButton = QPushButton("統計表IDの一覧を表示する")
            self.bottom_right_form.addRow(show_ids_btn)
            show_ids_btn.clicked.connect(self.show_lst_of_ids)
            # 統計表IDの一覧をフィルターにかける
            filter_ids_btn: QPushButton = QPushButton("統計表IDの一覧をフィルターにかける")
            self.bottom_right_form.addRow(filter_ids_btn)
            filter_ids_btn.clicked.connect(self.filter_lst_of_ids)
            # フィルターのキーワード
            self.keyword_text: QPlainTextEdit = QPlainTextEdit()
            self.keyword_text.textChanged.connect(self._get_keyword)
            self.bottom_right_form.addRow(QLabel("フィルターのキーワード\n(1行につき、1つのキーワード): "), self.keyword_text)
            # 検索方法
            self.match_type_combo: QComboBox = QComboBox()
            for key, desc in self.obj_of_cls.dct_of_match_type.items():
                self.match_type_combo.addItem(f"{key}: {desc}", userData=key)
            self.match_type_combo.currentIndexChanged.connect(self._get_match_type)
            self._get_match_type(0)
            self.bottom_right_form.addRow(QLabel("検索方法: "), self.match_type_combo)
            # 抽出方法
            self.logic_type_combo: QComboBox = QComboBox()
            for key, desc in self.obj_of_cls.dct_of_logic_type.items():
                self.logic_type_combo.addItem(f"{key}: {desc}", userData=key)
            self.logic_type_combo.currentIndexChanged.connect(self._get_logic_type)
            self._get_logic_type(0)
            self.bottom_right_form.addRow(QLabel("抽出方法: "), self.logic_type_combo)
            # 指定の統計表を表示する
            show_table_btn: QPushButton = QPushButton("統計表を表示する")
            self.bottom_right_form.addRow(show_table_btn)
            show_table_btn.clicked.connect(self.show_table)
            # 指定の統計表をフィルターにかける
            filter_table_btn: QPushButton = QPushButton("統計表をフィルターにかける")
            self.bottom_right_form.addRow(filter_table_btn)
            filter_table_btn.clicked.connect(self.filter_table)
            # 指定の統計表をCSVファイルに出力する
            output_btn: QPushButton = QPushButton("統計表を出力する")
            self.bottom_right_form.addRow(output_btn)
            output_btn.clicked.connect(self.output_table)
            # クレジット
            credit_area: QVBoxLayout = QVBoxLayout()
            self.main_layout.addLayout(credit_area)
            credit_notation: QLabel = QLabel("\n".join(self.obj_of_cls.credit_text))
            credit_area.addWidget(credit_notation)
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    @Slot(QModelIndex)
    def _get_id_from_lst(self, index: QModelIndex) -> None:
        """一覧から統計表IDを取得します"""
        try:
            if index is None:
                raise Exception("指定した統計表IDを取得できませんでした。")
            # 行番号
            r: int = index.row()
            # 列番号
            # 統計表ID
            c_of_id: int = 0
            # 統計名
            c_of_stat_name: int = 1
            # 表題
            c_of_title: int = 2
            self.obj_of_cls.STATS_DATA_ID = self.top_left_model.item(r, c_of_id).text()
            self.obj_of_cls.STAT_NAME = self.top_left_model.item(r, c_of_stat_name).text()
            self.obj_of_cls.TITLE = self.top_left_model.item(r, c_of_title).text()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            pass
        finally:
            self._show_info(
                f"選択された統計表ID: {self.obj_of_cls.STATS_DATA_ID}\n統計名: {self.obj_of_cls.STAT_NAME}\n表題: {self.obj_of_cls.TITLE}"
            )

    def _setup_second_ui(self) -> bool:
        """2番目のUser Interfaceを設定します"""
        result: bool = False
        try:
            self.top_left_container: QWidget = QWidget()
            self.top_left_container_layout: QVBoxLayout = QVBoxLayout(self.top_left_container)
            self.top_left_scroll_area.setWidget(self.top_left_container)
            self.top_left_table: QTableView = QTableView()
            self.top_left_container_layout.addWidget(self.top_left_table)
            self.top_left_model: QStandardItemModel = QStandardItemModel()
            # ヘッダーを追加する
            self.top_left_model.setHorizontalHeaderLabels(self.obj_of_cls.header_of_ids_l)
            self.top_left_table.setModel(self.top_left_model)
            self.top_left_table.clicked.connect(self._get_id_from_lst)
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def _setup_third_ui(self) -> bool:
        """3番目のUser Interfaceを設定します"""
        result: bool = False
        try:
            if self.obj_of_cls.pd_df is None:
                raise Exception("統計表を表示してください。")
            self.bottom_left_container: QWidget = QWidget()
            self.bottom_left_container_layout: QVBoxLayout = QVBoxLayout(self.bottom_left_container)
            self.bottom_left_scroll_area.setWidget(self.bottom_left_container)
            self.bottom_left_table: QTableView = QTableView(self)
            self.bottom_left_container_layout.addWidget(QLabel(f"統計表ID: {self.obj_of_cls.STATS_DATA_ID}"))
            self.bottom_left_container_layout.addWidget(QLabel(f"統計名: {self.obj_of_cls.STAT_NAME}"))
            self.bottom_left_container_layout.addWidget(QLabel(f"表題: {self.obj_of_cls.TITLE}"))
            self.bottom_left_container_layout.addWidget(self.bottom_left_table)
            self.bottom_left_model: QStandardItemModel = QStandardItemModel()
            # ヘッダーを追加する
            self.bottom_left_model.setHorizontalHeaderLabels(self.obj_of_cls.pd_df.columns.tolist())
            for r in self.obj_of_cls.pd_df.itertuples(index=False):
                items = [QStandardItem(str(v)) for v in r]
                self.bottom_left_model.appendRow(items)
            self.bottom_left_table.setModel(self.bottom_left_model)
            self.bottom_left_table.resizeColumnsToContents()
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def _check_first_form(self) -> bool:
        """1番目のフォームの入力を確認します"""
        result: bool = False
        try:
            if self.obj_of_cls.APP_ID == "":
                raise Exception("政府統計のAPIのアプリケーションIDを取得して、入力してください。https://www.e-stat.go.jp/")
            if not self.obj_of_cls.lst_of_data_type:
                raise Exception("データタイプを選択してください。")
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def _check_second_form(self) -> bool:
        """2番目のフォームの入力を確認します"""
        result: bool = False
        try:
            if not self.obj_of_cls.lst_of_match_type:
                raise Exception("検索方法を選択してください。")
            if not self.obj_of_cls.lst_of_keyword:
                raise Exception("キーワードを入力してください。")
            if not self.obj_of_cls.lst_of_logic_type:
                raise Exception("抽出方法を選択してください。")
            if len(self.obj_of_cls.lst_of_keyword) == 1:
                # 抽出方法はORのみ
                self.logic_type_combo.setCurrentIndex(0)
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def _clear_widget(self, widget: QWidget | None) -> bool:
        """ウィジェットの中身を安全に削除します"""
        result: bool = False
        try:
            if widget is None:
                raise Exception("Widget is None.")
            # QScrollArea
            if isinstance(widget, QScrollArea):
                inner: QWidget | None = widget.takeWidget()
                if inner is not None:
                    inner.deleteLater()
            else:
                layout: QLayout | None = widget.layout()
                if layout is not None:
                    self._clear_layout(layout)
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def _clear_layout(self, layout: QLayout) -> bool:
        """レイアウトの中身を安全に削除します"""
        result: bool = False
        try:
            while layout.count():
                item: QLayoutItem | None = layout.takeAt(0)
                if item is not None:
                    child_widget: QWidget | None = item.widget()
                    if child_widget is not None:
                        child_widget.deleteLater()
                    else:
                        child_layout: QLayout | None = item.layout()
                        if child_layout is not None:
                            self._clear_layout(child_layout)
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    @Slot()
    def _get_app_id(self) -> None:
        """アプリケーションIDを取得します"""
        try:
            tmp: str = self.app_id_text.text().strip()
            if not re.fullmatch(r"[a-z0-9]+", tmp):
                raise Exception("以下の文字で入力してください。\n* 半角英字小文字\n* 数字")
            self.obj_of_cls.APP_ID = tmp
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            pass
        finally:
            pass

    @Slot(int)
    def _get_data_type(self, index: int) -> None:
        """データタイプを取得します"""
        try:
            key: str = self.data_type_combo.itemData(index)
            desc: str = self.obj_of_cls.dct_of_data_type[key]
            self.obj_of_cls.lst_of_data_type = [key, desc]
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            pass
        finally:
            pass

    @Slot(int)
    def _get_get_type(self, index: int) -> None:
        """取得方法を取得します"""
        try:
            key: str = self.get_type_combo.itemData(index)
            desc: str = self.obj_of_cls.dct_of_get_type[key]
            self.obj_of_cls.lst_of_get_type = [key, desc]
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            pass
        finally:
            pass

    @Slot(int)
    def _get_match_type(self, index: int) -> None:
        """検索方法を取得します"""
        try:
            key: str = self.match_type_combo.itemData(index)
            desc: str = self.obj_of_cls.dct_of_match_type[key]
            self.obj_of_cls.lst_of_match_type = [key, desc]
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            pass
        finally:
            pass

    @Slot(int)
    def _get_logic_type(self, index: int) -> None:
        """抽出方法を取得します"""
        try:
            key: str = self.logic_type_combo.itemData(index)
            desc: str = self.obj_of_cls.dct_of_logic_type[key]
            self.obj_of_cls.lst_of_logic_type = [key, desc]
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            pass
        finally:
            pass

    @Slot()
    def _get_keyword(self) -> None:
        """キーワードを取得します"""
        try:
            self.obj_of_cls.lst_of_keyword = [line.strip() for line in self.keyword_text.toPlainText().splitlines() if line.strip()]
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            pass
        finally:
            pass

    @Slot(str)
    def _show_error_on_getting_ids(self, error: str) -> None:
        """統計表IDの一覧を取得する際のエラーを表示します"""
        # 取得ボタンを有効化する
        self.get_ids_btn.setEnabled(True)
        self._show_error(error)

    @Slot(bool)
    def _show_result_after_getting_ids(self, flag: bool) -> None:
        """統計表IDの一覧を取得した後の結果を表示します"""
        # キャンセルボタンを無効化する
        self.cancel_getting_ids_btn.setEnabled(False)
        # 取得ボタンを有効化する
        self.get_ids_btn.setEnabled(True)
        self._show_result(self.get_lst_of_ids.__doc__, flag)

    @Slot()
    def _cleanup_after_getting_ids(self) -> None:
        """統計表IDの一覧を取得した後にクリーンアップします"""
        self.worker_of_getting_ids = None
        self.thread_of_getting_ids = None

    @Slot()
    def get_lst_of_ids(self) -> bool:
        """統計表IDの一覧を取得します"""
        result: bool = False
        try:
            if self.thread_of_getting_ids is not None and self.thread_of_getting_ids.isRunning():
                self._show_error("統計表IDの一覧を取得しています。")
                raise
            self._check_first_form()
            # 取得方法は非同期のみ
            self.get_type_combo.setCurrentIndex(0)
            self.worker_of_getting_ids = GetIdsWorker(
                self.obj_of_lt.logger, self.obj_of_cls.APP_ID, self.obj_of_cls.lst_of_data_type, self.obj_of_cls.lst_of_get_type
            )
            self.thread_of_getting_ids = QThread()
            self.worker_of_getting_ids.moveToThread(self.thread_of_getting_ids)
            # キャンセルボタンを有効化する
            self.cancel_getting_ids_btn.setEnabled(True)
            # 取得ボタンを無効化する
            self.get_ids_btn.setEnabled(False)
            self.thread_of_getting_ids.started.connect(self.worker_of_getting_ids.run)
            self.worker_of_getting_ids.log.connect(self._append_log, Qt.ConnectionType.QueuedConnection)
            self.worker_of_getting_ids.finished.connect(self.thread_of_getting_ids.quit)
            self.worker_of_getting_ids.error.connect(self.thread_of_getting_ids.quit)
            self.worker_of_getting_ids.error.connect(self._show_error_on_getting_ids)
            self.worker_of_getting_ids.finished.connect(self._show_result_after_getting_ids)
            self.thread_of_getting_ids.finished.connect(self.worker_of_getting_ids.deleteLater)
            self.thread_of_getting_ids.finished.connect(self.thread_of_getting_ids.deleteLater)
            self.thread_of_getting_ids.finished.connect(self._cleanup_after_getting_ids)
            self.thread_of_getting_ids.start()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    @Slot()
    def cancel_getting_lst_of_ids(self) -> None:
        """統計表IDの一覧の取得をキャンセルします"""
        if self.worker_of_getting_ids is not None:
            self.worker_of_getting_ids.cancel()
        # キャンセルボタンを無効化する
        self.cancel_getting_ids_btn.setEnabled(False)

    @Slot()
    def show_lst_of_ids(self) -> bool:
        """統計表IDの一覧を表示します"""
        result: bool = False
        try:
            csv_files: list = list(self.obj_of_cls.folder_p_of_ids.glob("*.csv"))
            if not csv_files:
                raise Exception("統計表IDの一覧を取得してください。")
            self._clear_widget(self.top_left_scroll_area)
            self._setup_second_ui()
            for csv_file in csv_files:
                reader: TextFileReader = pd.read_csv(filepath_or_buffer=str(csv_file), chunksize=1, dtype=str)
                for chunk in reader:
                    for _, row in chunk.iterrows():
                        items: list = [QStandardItem(str(v)) for v in row]
                        self.top_left_model.appendRow(items)
            self.top_left_table.resizeColumnsToContents()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            self._show_result(self.show_lst_of_ids.__doc__, result)
        return result

    @Slot()
    def filter_lst_of_ids(self) -> bool:
        """統計表IDの一覧をフィルターにかけます"""
        result: bool = False
        try:
            csv_files: list = list(self.obj_of_cls.folder_p_of_ids.glob(pattern="*.csv"))
            if not csv_files:
                raise Exception("統計表IDの一覧を取得してください。")
            self._check_second_form()
            self._clear_widget(self.top_left_scroll_area)
            self._setup_second_ui()
            for csv_file in csv_files:
                reader: TextFileReader = pd.read_csv(filepath_or_buffer=str(csv_file), chunksize=1, dtype=str)
                for chunk in reader:
                    pd_df: pd.DataFrame = self.obj_of_cls.filter_pd_df(chunk)
                    for _, row in pd_df.iterrows():
                        items: list = [QStandardItem(str(v)) for v in row]
                        self.top_left_model.appendRow(items)
            self.top_left_table.resizeColumnsToContents()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            self._show_result(self.filter_lst_of_ids.__doc__, result)
        return result

    @Slot()
    def show_table(self) -> bool:
        """指定の統計表を表示します"""
        result: bool = False
        try:
            if self.obj_of_cls.STATS_DATA_ID == "":
                raise Exception("統計表IDを選択してください。")
            self._check_first_form()
            self._clear_widget(self.bottom_left_scroll_area)
            # 取得方法は同期のみ
            self.get_type_combo.setCurrentIndex(1)
            self.obj_of_cls.get_table_from_api()
            self._setup_third_ui()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
            self.obj_of_cls.show_table()
        finally:
            self._show_result(self.show_table.__doc__, result)
        return result

    @Slot()
    def filter_table(self) -> bool:
        """指定の統計表をフィルターにかけます"""
        result: bool = False
        try:
            if self.obj_of_cls.pd_df is None:
                raise Exception("統計表を表示してください。")
            self._check_second_form()
            self.obj_of_cls.pd_df = self.obj_of_cls.filter_pd_df(self.obj_of_cls.pd_df)
            self._clear_widget(self.bottom_left_scroll_area)
            self._setup_third_ui()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
            self.obj_of_cls.show_table()
        finally:
            self._show_result(self.filter_table.__doc__, result)
        return result

    @Slot()
    def output_table(self) -> bool:
        """指定の統計表をファイルに出力します"""
        result: bool = False
        try:
            if self.obj_of_cls.pd_df is None:
                raise Exception("統計表を表示してください。")
            self.obj_of_cls.output_table_to_csv()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            self._show_result(self.output_table.__doc__, result)
        return result


def create_window() -> MainApp_Of_GJGS:
    window: MainApp_Of_GJGS = MainApp_Of_GJGS()
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
        window: MainApp_Of_GJGS = create_window()
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
