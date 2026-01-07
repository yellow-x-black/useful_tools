from logging import Logger
from pathlib import Path


class GetFileList:
    """指定のフォルダ内のファイルのリストを取得します"""

    def __init__(self, logger: Logger):
        """初期化します"""
        self.log: Logger = logger
        self.log.info(self.__class__.__doc__)
        # フォルダパス
        self.folder_path: str = ""
        # 再帰的に検索するかどうか
        self.recursive: bool = False
        # 検索パターン
        self.pattern: str = ""
        # ファイルパスのリスト
        self.lst_file_before: list = []
        self.lst_file_after: list = []
        # ファイルの数
        self.num_of_f_before: int = 0
        self.num_of_f_after: int = 0

    def search_directly_under_folder(self) -> bool:
        """フォルダ直下を検索します"""
        result: bool = False
        try:
            self.log.info(f"起点のフォルダパス: {self.folder_path}")
            self.log.info(f"再帰的に検索: {'する' if self.recursive else 'しない'}")
            RECURSIVE: str = "**/*" if self.recursive else "*"
            self.lst_file_before = [str(f) for f in Path(self.folder_path).glob(RECURSIVE) if f.is_file()]
            if not self.lst_file_before:
                raise Exception("フォルダにファイルがありませんでした。")
            self.num_of_f_before = len(self.lst_file_before)
            self.log.info(f"{self.num_of_f_before}件のファイルがあります。")
            self.log.info("\n".join(self.lst_file_before))
        except Exception:
            raise
        else:
            result = True
            self.log.info(f"***{self.search_directly_under_folder.__doc__} => 成功しました。***")
        finally:
            pass
        return result

    def extract_by_pattern(self) -> bool:
        """検索パターンで抽出します"""
        result: bool = False
        try:
            self.log.info(f"検索パターン: {self.pattern if self.pattern else "なし"}")
            self.lst_file_after = [f for f in self.lst_file_before if self.pattern in f]
            if not self.lst_file_after:
                raise Exception("検索パターンによる抽出結果がありませんでした。")
            self.num_of_f_after = len(self.lst_file_after)
            self.log.info(f"{self.num_of_f_after}件のファイルが抽出されました。")
            self.log.info("\n".join(self.lst_file_after))
        except Exception:
            raise
        else:
            result = True
            self.log.info(f"***{self.extract_by_pattern.__doc__} => 成功しました。***")
        finally:
            pass
        return result
