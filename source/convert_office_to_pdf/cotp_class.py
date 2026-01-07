from logging import Logger
from pathlib import Path
from typing import Any

from comtypes.client import CreateObject


class ConvertOfficeToPDF:
    """
    オフィスファイルをPDFに一括変換します
    Windows + Microsoft Office(デスクトップ版)が必要です
    """

    def __init__(self, logger: Logger):
        """初期化します"""
        self.log: Logger = logger
        self.log.info(self.__class__.__doc__)
        # 拡張子の辞書
        self.file_types: dict = {
            "Excel": [".xls", ".xlsx"],
            "Word": [".doc", ".docx"],
            "Powerpoint": [".ppt", ".pptx"],
        }
        # 拡張子のリスト
        self.valid_exts: list = sum(self.file_types.values(), [])
        # 拡張子をログに出力する
        self.log.info("以下が変換元に指定できるファイルの拡張子の一覧です。\n")
        for key, info in self.file_types.items():
            values: str = ""
            for value in info:
                values += f"{value}, "
            values = values.rstrip(", ")
            self.log.info(f"{key}: {values}")
        # 拡張子をログに出力した後は、改行する
        self.log.info("")
        # 変換元のフォルダパス
        self.folder_path_from: str = ""
        # 変換先のフォルダパス
        self.folder_path_to: str = ""
        # フィルター後のファイルのリスト
        self.filtered_lst_of_f: list = []
        # 変換元のフォルダのファイルの数
        self.number_of_f: int = 0
        # ファイルリストのポインタ
        self.p: int = 0
        # 変換元のファイルパス
        self.current_file_path_from: str = ""
        # 変換先のファイルパス
        self.current_file_path_to: str = ""
        # 処理したファイルの数
        self.count: int = 0
        # 処理が成功したファイルの数
        self.success: int = 0
        # 全てのファイルを変換できたかどうか
        self.complete: bool = False

    def _set_file_path(self) -> bool:
        """ファイルパスを設定します"""
        result: bool = False
        try:
            self.current_file_path_from = self.filtered_lst_of_f[self.p]
            current_file_from_p: Path = Path(self.current_file_path_from)
            current_file_to_p: Path = Path(self.folder_path_to) / f"{current_file_from_p.stem}.pdf"
            self.current_file_path_to = str(current_file_to_p)
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def create_file_lst(self) -> bool:
        """ファイルリストを作成します"""
        result: bool = False
        try:
            # 指定のフォルダにあるファイルパスのリストから指定の拡張子で抽出する
            self.filtered_lst_of_f = [str(f) for f in Path(self.folder_path_from).glob("*") if f.suffix.lower() in self.valid_exts]
            self.number_of_f = len(self.filtered_lst_of_f)
            if not self.number_of_f:
                raise Exception("変換元のファイルがありません。")
            self._set_file_path()
        except Exception:
            raise
        else:
            result = True
            self.log.info(f"***{self.create_file_lst.__doc__} => 成功しました。***")
            self.log.info(f"{self.number_of_f}件のファイルが見つかりました。")
            self.log.info(f"変換先のフォルダ: {self.folder_path_to}")
        finally:
            # 初期化する
            self.p = 0
            self.count = 0
            self.success = 0
        return result

    def move_to_previous_file(self) -> bool:
        """前のファイルへ"""
        result: bool = False
        try:
            if not self.p:
                self.p = self.number_of_f - 1
            else:
                self.p -= 1
            self._set_file_path()
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def move_to_next_file(self) -> bool:
        """次のファイルへ"""
        result: bool = False
        try:
            if self.p == self.number_of_f - 1:
                self.p = 0
            else:
                self.p += 1
            self._set_file_path()
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def handle_file(self) -> bool:
        """ファイルの種類を判定して、各処理を実行します"""

        def _with_excel() -> bool:
            """ExcelをPDFに変換します"""
            result: bool = False
            PDF_NUMBER_OF_EXCEL: int = 0
            self.log.info(f"* [{self.count + 1} / {self.number_of_f}] {_with_excel.__doc__}: ")
            self.log.info(f"{self.current_file_path_from} => {self.current_file_path_to}")
            try:
                obj: Any = CreateObject("Excel.Application")
                f: Any = obj.Workbooks.Open(self.current_file_path_from, ReadOnly=False)
                f.ExportAsFixedFormat(Filename=self.current_file_path_to, Type=PDF_NUMBER_OF_EXCEL)
            except Exception:
                self.log.error("***失敗しました。***")
                raise
            else:
                result = True
                self.log.info("***成功しました。***")
            finally:
                pass
            if f:
                f.Close()
            if obj:
                obj.Quit()
            return result

        def _with_word() -> bool:
            """WordをPDFに変換します"""
            result: bool = False
            PDF_NUMBER_OF_WORD: int = 17
            self.log.info(f"* [{self.count + 1} / {self.number_of_f}] {_with_word.__doc__}: ")
            self.log.info(f"{self.current_file_path_from} => {self.current_file_path_to}")
            try:
                obj: Any = CreateObject("Word.Application")
                f: Any = obj.Documents.Open(self.current_file_path_from, ReadOnly=False)
                f.ExportAsFixedFormat(
                    OutputFileName=self.current_file_path_to,
                    ExportFormat=PDF_NUMBER_OF_WORD,
                )
            except Exception:
                self.log.error("***失敗しました。***")
                raise
            else:
                result = True
                self.log.info("***成功しました。***")
            finally:
                pass
            if f:
                f.Close()
            if obj:
                obj.Quit()
            return result

        def _with_powerpoint() -> bool:
            """PowerPointをPDFに変換します"""
            result: bool = False
            PDF_NUMBER_OF_POWERPOINT: int = 2
            self.log.info(f"* [{self.count + 1} / {self.number_of_f}] {_with_powerpoint.__doc__}: ")
            self.log.info(f"{self.current_file_path_from} => {self.current_file_path_to}")
            try:
                obj: Any = CreateObject("PowerPoint.Application")
                f: Any = obj.Presentations.Open(self.current_file_path_from, ReadOnly=False)
                f.ExportAsFixedFormat(
                    Path=self.current_file_path_to,
                    FixedFormatType=PDF_NUMBER_OF_POWERPOINT,
                )
            except Exception:
                self.log.error("***失敗しました。***")
                raise
            else:
                result = True
                self.log.info("***成功しました。***")
            finally:
                pass
            if f:
                f.Close()
            if obj:
                obj.Quit()
            return result

        result: bool = False
        try:
            ext: str = Path(self.current_file_path_from).suffix.lower()
            match ext:
                case var if var in self.file_types["Excel"]:
                    result = _with_excel()
                case var if var in self.file_types["Word"]:
                    result = _with_word()
                case var if var in self.file_types["Powerpoint"]:
                    result = _with_powerpoint()
            self.count += 1
            if result:
                self.success += 1
            if self.count == self.number_of_f:
                if self.success == self.number_of_f:
                    self.complete = True
                    self.log.info("全てのファイルの変換が完了しました。")
                else:
                    raise Exception("一部のファイルの変換が失敗しました。")
        except Exception:
            raise
        else:
            pass
        finally:
            pass
        return result
