import asyncio
import csv
import logging
import re
import sys
from pathlib import Path
from typing import Any

import httpx
import pandas
from PySide6.QtCore import QModelIndex, QObject, QThread, Signal
from PySide6.QtGui import QFont, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
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

from source.common.common import DatetimeTools, GUITools, LogTools
from source.get_government_statistics.g2s_class import GetGovernmentStatistics


class GetIdsWorker(QObject):
    """統計表IDの一覧を取得する処理の非同期ワーカー"""

    finished: Signal = Signal(bool)
    error: Signal = Signal(str)

    def __init__(self, obj_of_cls: Any):
        """初期化します"""
        super().__init__()
        self.obj_of_cls = obj_of_cls

    def run(self):
        """実行します"""
        result: bool = False
        try:
            loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.obj_of_cls.write_stats_data_ids_to_file())
        except httpx.HTTPStatusError as e:
            self.error.emit(f"HTTPStatusError: \n{str(e)}")
        except httpx.RequestError as e:
            self.error.emit(f"RequestError: \n{str(e)}")
        except Exception as e:
            self.error.emit(f"Exception: \n{str(e)}")
        else:
            result = True
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        self.finished.emit(result)

    def cancel(self):
        """キャンセルします"""
        self.obj_of_cls.cancel = True


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


class MainApp_Of_G2S(QMainWindow):
    def __init__(self):
        """初期化します"""
        super().__init__()
        self.obj_of_lt: LogTools = LogTools()
        self.obj_of_cls: GetGovernmentStatistics = GetGovernmentStatistics(self.obj_of_lt.logger)
        self._setup_first_ui()
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

    def _setup_first_ui(self) -> bool:
        """1番目のUser Interfaceを設定します"""
        result: bool = False
        try:
            # タイトル
            self.setWindowTitle("政府統計表示アプリ")
            central: QWidget = QWidget()
            self.setCentralWidget(central)
            # 主要
            self.main_layout: QVBoxLayout = QVBoxLayout(central)
            # 上
            self.first_element_title_area: QHBoxLayout = QHBoxLayout()
            self.main_layout.addLayout(self.first_element_title_area)
            self.first_element_title_area.addWidget(QLabel("統計表ID"))
            self.first_element_title_area.addWidget(QLabel("ログ"))
            self.top_layout: QHBoxLayout = QHBoxLayout()
            self.main_layout.addLayout(self.top_layout, 2)
            # 左上
            self.top_left_scroll_area: QScrollArea = QScrollArea()
            self.top_left_scroll_area.setWidgetResizable(True)
            self.top_layout.addWidget(self.top_left_scroll_area, 1)
            self._setup_second_ui()
            # 右上
            top_right_scroll_area: QScrollArea = QScrollArea()
            top_right_scroll_area.setWidgetResizable(True)
            self.top_layout.addWidget(top_right_scroll_area, 1)
            top_right_container: QWidget = QWidget()
            self.top_right_container_layout: QVBoxLayout = QVBoxLayout(top_right_container)
            top_right_scroll_area.setWidget(top_right_container)
            self.log_area: QTextEdit = QTextEdit()
            self.log_area.setReadOnly(True)
            self.top_right_container_layout.addWidget(self.log_area)
            # 下
            self.second_element_title_area: QHBoxLayout = QHBoxLayout()
            self.main_layout.addLayout(self.second_element_title_area)
            self.second_element_title_area.addWidget(QLabel("統計表"))
            self.second_element_title_area.addWidget(QLabel("機能"))
            self.bottom_layout: QHBoxLayout = QHBoxLayout()
            self.main_layout.addLayout(self.bottom_layout, 3)
            # 統計表
            self.table_scroll_area: QScrollArea = QScrollArea()
            self.table_scroll_area.setWidgetResizable(True)
            self.bottom_layout.addWidget(self.table_scroll_area, 1)
            # 関数
            func_scroll_area: QScrollArea = QScrollArea()
            func_scroll_area.setWidgetResizable(True)
            self.bottom_layout.addWidget(func_scroll_area, 1)
            func_container: QWidget = QWidget()
            func_container_layout: QVBoxLayout = QVBoxLayout(func_container)
            func_scroll_area.setWidget(func_container)
            func_area: QFormLayout = QFormLayout()
            func_container_layout.addLayout(func_area)
            # アプリケーションID
            self.app_id_text: QLineEdit = QLineEdit()
            self.app_id_text.editingFinished.connect(self._get_app_id)
            func_area.addRow(QLabel("アプリケーションID: "), self.app_id_text)
            # データタイプ
            self.data_type_combo: QComboBox = QComboBox()
            for key, desc in self.obj_of_cls.dct_of_data_type.items():
                self.data_type_combo.addItem(f"{key}: {desc}", userData=key)
            self.data_type_combo.currentIndexChanged.connect(self._get_data_type)
            self._get_data_type(0)
            func_area.addRow(QLabel("データタイプ: "), self.data_type_combo)
            # 取得方法
            self.get_type_combo: QComboBox = QComboBox()
            for key, desc in self.obj_of_cls.dct_of_get_type.items():
                self.get_type_combo.addItem(f"{key}: {desc}", userData=key)
            self.get_type_combo.currentIndexChanged.connect(self._get_get_type)
            self._get_get_type(0)
            func_area.addRow(QLabel("取得方法: "), self.get_type_combo)
            # 統計表IDの一覧を取得する
            get_ids_btn: QPushButton = QPushButton("統計表IDの一覧を取得する")
            get_ids_btn.clicked.connect(self.get_lst_of_ids)
            # 統計表IDの一覧の取得をキャンセルする
            cancel_getting_ids_btn: QPushButton = QPushButton("統計表IDの一覧の取得をキャンセルする")
            cancel_getting_ids_btn.clicked.connect(self.cancel_getting_lst_of_ids)
            func_area.addRow(get_ids_btn, cancel_getting_ids_btn)
            # 統計表IDの一覧を表示する
            show_ids_btn: QPushButton = QPushButton("統計表IDの一覧を表示する")
            func_area.addRow(show_ids_btn)
            show_ids_btn.clicked.connect(self.show_lst_of_ids)
            # 統計表IDの一覧をフィルターにかける
            filter_ids_btn: QPushButton = QPushButton("統計表IDの一覧をフィルターにかける")
            func_area.addRow(filter_ids_btn)
            filter_ids_btn.clicked.connect(self.filter_lst_of_ids)
            # フィルターのキーワード
            self.keyword_text: QPlainTextEdit = QPlainTextEdit()
            self.keyword_text.textChanged.connect(self._get_keyword)
            func_area.addRow(QLabel("フィルターのキーワード\n(1行につき、1つのキーワード): "), self.keyword_text)
            # 検索方法
            self.match_type_combo: QComboBox = QComboBox()
            for key, desc in self.obj_of_cls.dct_of_match_type.items():
                self.match_type_combo.addItem(f"{key}: {desc}", userData=key)
            self.match_type_combo.currentIndexChanged.connect(self._get_match_type)
            self._get_match_type(0)
            func_area.addRow(QLabel("検索方法: "), self.match_type_combo)
            # 抽出方法
            self.logic_type_combo: QComboBox = QComboBox()
            for key, desc in self.obj_of_cls.dct_of_logic_type.items():
                self.logic_type_combo.addItem(f"{key}: {desc}", userData=key)
            self.logic_type_combo.currentIndexChanged.connect(self._get_logic_type)
            self._get_logic_type(0)
            func_area.addRow(QLabel("抽出方法: "), self.logic_type_combo)
            # 指定の統計表を表示する
            show_table_btn: QPushButton = QPushButton("統計表を表示する")
            func_area.addRow(show_table_btn)
            show_table_btn.clicked.connect(self.show_table)
            # 指定の統計表をフィルターにかける
            filter_table_btn: QPushButton = QPushButton("統計表をフィルターにかける")
            func_area.addRow(filter_table_btn)
            filter_table_btn.clicked.connect(self.filter_table)
            # 指定の統計表をCSVファイルに出力する
            output_btn: QPushButton = QPushButton("統計表を出力する")
            func_area.addRow(output_btn)
            output_btn.clicked.connect(self.output_table)
            # クレジット
            credit_area: QVBoxLayout = QVBoxLayout()
            self.main_layout.addLayout(credit_area)
            credit_notation: QLabel = QLabel(self.obj_of_cls.credit_text)
            credit_area.addWidget(credit_notation)
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    def _get_id_from_lst(self, index: QModelIndex):
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
            self.obj_of_cls.STATS_DATA_ID = self.model.item(r, c_of_id).text()
            self.obj_of_cls.STAT_NAME = self.model.item(r, c_of_stat_name).text()
            self.obj_of_cls.TITLE = self.model.item(r, c_of_title).text()
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
            self.lst_of_ids: QTableView = QTableView()
            self.top_left_container_layout.addWidget(self.lst_of_ids)
            self.model: QStandardItemModel = QStandardItemModel()
            # ヘッダーを追加する
            self.model.setHorizontalHeaderLabels(self.obj_of_cls.header_of_ids_l)
            self.lst_of_ids.setModel(self.model)
            self.lst_of_ids.clicked.connect(self._get_id_from_lst)
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
            self.table_container: QWidget = QWidget()
            self.table_container_layout: QVBoxLayout = QVBoxLayout(self.table_container)
            self.table_scroll_area.setWidget(self.table_container)
            self.stats_table: QTableView = QTableView(self)
            self.table_container_layout.addWidget(QLabel(f"統計表ID: {self.obj_of_cls.STATS_DATA_ID}"))
            self.table_container_layout.addWidget(QLabel(f"統計名: {self.obj_of_cls.STAT_NAME}"))
            self.table_container_layout.addWidget(QLabel(f"表題: {self.obj_of_cls.TITLE}"))
            self.table_container_layout.addWidget(self.stats_table)
            model: QStandardItemModel = QStandardItemModel()
            # ヘッダーを追加する
            model.setHorizontalHeaderLabels(self.obj_of_cls.df.columns.tolist())
            for r in self.obj_of_cls.df.itertuples(index=False):
                items = [QStandardItem(str(v)) for v in r]
                model.appendRow(items)
            self.stats_table.setModel(model)
            self.stats_table.resizeColumnsToContents()
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
            if self.obj_of_cls.lst_of_match_type[self.obj_of_cls.KEY] != "検索しない":
                if not self.obj_of_cls.lst_of_keyword:
                    raise Exception("キーワードを入力してください。")
                if len(self.obj_of_cls.lst_of_keyword) > 1:
                    if not self.obj_of_cls.lst_of_logic_type:
                        raise Exception("抽出方法を選択してください。")
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
                raise
            # QScrollArea
            if isinstance(widget, QScrollArea):
                inner: QWidget = widget.takeWidget()
                if inner:
                    inner.deleteLater()
            else:
                layout: QLayout | None = widget.layout()
                if layout:
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
                item: QLayoutItem = layout.takeAt(0)
                child_widget: QWidget | None = item.widget()
                if child_widget:
                    child_widget.deleteLater()
                    continue
                child_layout: QLayout = item.layout()
                if child_layout:
                    self._clear_layout(child_layout)
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def _get_app_id(self):
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

    def _get_data_type(self, index: int):
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

    def _get_get_type(self, index: int):
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

    def _get_match_type(self, index: int):
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

    def _get_logic_type(self, index: int):
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

    def _get_keyword(self):
        """キーワードを取得します"""
        try:
            self.obj_of_cls.lst_of_keyword = [line.strip() for line in self.keyword_text.toPlainText().splitlines() if line.strip()]
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            pass
        finally:
            pass

    def get_lst_of_ids(self) -> bool:
        """統計表IDの一覧を取得します"""
        result: bool = False
        try:
            self._check_first_form()
            # 取得方法は非同期のみ
            self.get_type_combo.setCurrentIndex(0)
            self.worker: GetIdsWorker = GetIdsWorker(self.obj_of_cls)
            self.thread: QThread = QThread()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.error.connect(self._show_error)
            self.worker.finished.connect(lambda ok: self._show_result(self.get_lst_of_ids.__doc__, ok))
            self.thread.start()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            pass
        return result

    def cancel_getting_lst_of_ids(self):
        """統計表IDの一覧の取得をキャンセルします"""
        if hasattr(self, "worker") and self.worker is not None:
            self.worker.cancel()

    def show_lst_of_ids(self) -> bool:
        """統計表IDの一覧を表示します"""
        result: bool = False
        try:
            self._clear_widget(self.top_left_scroll_area)
            self._setup_second_ui()
            # 検索パターン
            PATTERN: str = "*.csv"
            csv_files = self.obj_of_cls.folder_p_of_ids.glob(PATTERN)
            if not any(csv_files):
                raise Exception("統計表IDの一覧を取得してください。")
            for csv_file in csv_files:
                with open(str(csv_file), newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    # ヘッダー行をスキップする
                    next(reader, None)
                    for row in reader:
                        items: list = [QStandardItem(str(cell)) for cell in row]
                        self.model.appendRow(items)
            self.lst_of_ids.resizeColumnsToContents()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            self._show_result(self.show_lst_of_ids.__doc__, result)
        return result

    def filter_lst_of_ids(self) -> bool:
        """統計表IDの一覧をフィルターにかけます"""
        result: bool = False
        try:
            self._check_second_form()
            self._clear_widget(self.top_left_scroll_area)
            self._setup_second_ui()
            # 検索パターン
            PATTERN: str = "*.csv"
            csv_files = self.obj_of_cls.folder_p_of_ids.glob(PATTERN)
            if not any(csv_files):
                raise Exception("統計表IDの一覧を取得してください。")
            for csv_file in csv_files:
                reader = pandas.read_csv(str(csv_file), chunksize=1, dtype=str)
                # ヘッダー行をスキップする
                next(reader, None)
                for chunk in reader:
                    df = self.obj_of_cls.filter_df(chunk)
                    for _, row in df.iterrows():
                        items: list = [QStandardItem(str(v)) for v in row]
                        self.model.appendRow(items)
            self.lst_of_ids.resizeColumnsToContents()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            self._show_result(self.filter_lst_of_ids.__doc__, result)
        return result

    def show_table(self) -> bool:
        """指定の統計表を表示します"""
        result: bool = False
        try:
            if self.obj_of_cls.STATS_DATA_ID == "":
                raise Exception("統計表IDを選択してください。")
            self._check_first_form()
            self._clear_widget(self.table_scroll_area)
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

    def filter_table(self) -> bool:
        """指定の統計表をフィルターにかけます"""
        result: bool = False
        try:
            if self.obj_of_cls.df is None:
                raise Exception("統計表を表示してください。")
            self._check_second_form()
            self._clear_widget(self.table_scroll_area)
            self.obj_of_cls.df = self.obj_of_cls.filter_df(self.obj_of_cls.df)
            self._setup_third_ui()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
            self.obj_of_cls.show_table()
        finally:
            self._show_result(self.filter_table.__doc__, result)
        return result

    def output_table(self) -> bool:
        """指定の統計表をファイルに出力します"""
        result: bool = False
        try:
            if self.obj_of_cls.df is None:
                raise Exception("統計表を表示してください。")
            self.obj_of_cls.output_table_to_csv()
        except Exception as e:
            self._show_error(f"error: \n{str(e)}")
        else:
            result = True
        finally:
            self._show_result(self.output_table.__doc__, result)
        return result


def create_window() -> MainApp_Of_G2S:
    window: MainApp_Of_G2S = MainApp_Of_G2S()
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
