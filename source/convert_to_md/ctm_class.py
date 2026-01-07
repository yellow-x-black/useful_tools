from logging import Logger
from pathlib import Path
from typing import Any

from markitdown import MarkItDown


class ConvertToMd:
    """
    markdownに一括変換します
    """

    def __init__(self, logger: Logger):
        """初期化します"""
        self.log: Logger = logger
        self.log.info(self.__class__.__doc__)
        # 拡張子の辞書
        self.file_types: dict = {
            "PDF": [".pdf"],
            "Excel": [".xlsx"],
            "Word": [".docx"],
            "PowerPoint": [".pptx"],
            "HTML": [".html"],
            "CSV": [".csv"],
            "JSON": [".json"],
            "XML": [".xml"],
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
        # マークダウンのオブジェクト
        self.md: MarkItDown = MarkItDown()
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
        # すべてのファイルを変換できたかどうか
        self.complete: bool = False

    def _set_file_path(self) -> bool:
        """ファイルパスを設定します"""
        result: bool = False
        try:
            self.current_file_path_from = self.filtered_lst_of_f[self.p]
            current_file_from_p: Path = Path(self.current_file_path_from)
            current_file_to_p: Path = Path(self.folder_path_to) / f"{current_file_from_p.stem}.md"
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

    def convert_file(self) -> bool:
        """変換します"""
        result: bool = False
        try:
            self.log.info(f"* [{self.count + 1} / {self.number_of_f}] {self.convert_file.__doc__}: ")
            self.log.info(f"{self.current_file_path_from} => {self.current_file_path_to}")
            try:
                doc: Any = self.md.convert(self.current_file_path_from)
                current_file_to_p: Path = Path(self.current_file_path_to)
                current_file_to_p.write_text(doc.text_content, encoding="utf-8")
            except Exception:
                self.log.error("***失敗しました。***")
                raise
            else:
                self.success += 1
                self.log.info("***成功しました。***")
            finally:
                self.count += 1
                if self.count == self.number_of_f:
                    if self.success == self.number_of_f:
                        self.complete = True
                        self.log.info("全てのファイルの変換が終了しました。")
                    else:
                        raise Exception("一部のファイルの変換が失敗しました。")
        except Exception:
            raise
        else:
            pass
        finally:
            pass
        return result
