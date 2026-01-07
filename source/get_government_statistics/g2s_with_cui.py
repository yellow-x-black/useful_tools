import asyncio
import re
import sys
from pathlib import Path
from typing import Any

from source.common.common import DatetimeTools, LogTools
from source.get_government_statistics.g2s_class import GetGovernmentStatistics


class GS_With_Cui:
    def __init__(self):
        """初期化します"""
        self.binary_choices: dict = {
            "yes": ["はい", "1", "Yes", "yes", "Y", "y"],
            "no": ["いいえ", "0", "No", "no", "N", "n"],
        }

    def _input_app_id(self) -> str:
        """アプリケーションIDを入力します"""
        while True:
            try:
                app_id: str = input("政府統計のAPIのアプリケーションIDを取得して、入力してください。https://www.e-stat.go.jp/: ").strip()
                if app_id == "":
                    raise Exception("アプリケーションIDが未入力です。")
                if not re.fullmatch(r"[a-z0-9]+", app_id):
                    raise Exception("以下の文字で入力してください。\n* 半角英字小文字\n* 数字")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"error: \n{str(e)}")
            else:
                break
            finally:
                pass
        return app_id

    def _select_element(self, elements: Any) -> list:
        """要素を選択します"""
        lst: list = []
        while True:
            try:
                match elements:
                    case dict():
                        # リストに変換する
                        lst = list(elements.items())
                        for i, (k, v) in enumerate(lst, start=1):
                            print(f"{i}. {k}: {v}")
                    case list():
                        lst = elements
                        for i, s in enumerate(lst, start=1):
                            print(f"{i}. {s}")
                    case _:
                        raise Exception("この変数の型は、対象外です。")
                text: str = input("番号を入力してください。: ").strip()
                if text == "":
                    raise Exception("番号が未入力です。")
                if not text.isdecimal():
                    raise Exception("数字を入力してください。")
                num: int = int(text)
                if num < 1 or num > len(lst):
                    raise Exception("入力した番号が範囲外です。")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"error: \n{str(e)}")
            else:
                break
            finally:
                pass
        return lst[num - 1]

    def _input_lst_of_text(self, msg: str) -> list:
        """複数の文字列を入力します"""
        lst: list = []
        try:
            while True:
                text: str = input(msg).strip()
                lst.append(text)
                keep: bool = self._input_bool("入力する文字列は、まだありますか？")
                if not keep:
                    if lst:
                        break
                    else:
                        print("文字列が何も入力されていません。")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"error: \n{str(e)}")
        else:
            pass
        finally:
            pass
        return lst

    def _input_stats_data_id(self) -> str:
        """統計表IDを入力します"""
        text: str = ""
        # 桁
        DIGIT: int = 10
        while True:
            try:
                text: str = input("統計表IDを入力してください。: ").strip()
                if text == "":
                    raise Exception("統計表IDが未入力です。")
                if not text.isdecimal():
                    raise Exception("数字を入力してください。")
                if len(text) != DIGIT:
                    raise Exception(f"{DIGIT}桁で入力してください。")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"error: \n{str(e)}")
            else:
                break
            finally:
                pass
        return text

    def _input_bool(self, msg: str) -> bool:
        """はいかいいえをを入力します"""
        result: bool = False
        while True:
            try:
                text: str = input(f"{msg}\n(Yes => y or No => n): ").strip()
                match text:
                    case var if var in self.binary_choices["yes"]:
                        result = True
                    case var if var in self.binary_choices["no"]:
                        pass
                    case _:
                        raise Exception("無効な入力です。")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"error: \n{str(e)}")
            else:
                break
            finally:
                pass
        return result


async def main() -> bool:
    """主要関数"""
    # ログを設定します
    result: bool = False
    try:
        obj_of_dt2: DatetimeTools = DatetimeTools()
        obj_of_lt: LogTools = LogTools()
        # ログフォルダのパス
        folder_p: Path = Path(__file__).parent / "__log__"
        # ログフォルダが存在しない場合は、作成します
        folder_p.mkdir(parents=True, exist_ok=True)
        # ログファイル名
        file_name: str = f"log_{obj_of_dt2._convert_for_file_name()}.log"
        file_p: Path = folder_p / file_name
        obj_of_lt.file_path_of_log = str(file_p)
        obj_of_lt._setup_file_handler(obj_of_lt.file_path_of_log)
        obj_of_lt._setup_stream_handler()
    except Exception as e:
        print(f"error: \n{str(e)}")
        return result
    else:
        pass
    finally:
        pass
    # 処理の本体部分
    obj_with_cui: GS_With_Cui = GS_With_Cui()
    obj_of_cls: GetGovernmentStatistics = GetGovernmentStatistics(obj_of_lt.logger)
    while True:
        try:
            obj_of_cls.APP_ID = obj_with_cui._input_app_id()
            obj_of_cls.lst_of_data_type = obj_with_cui._select_element(obj_of_cls.dct_of_data_type)
            if obj_with_cui._input_bool(f"{obj_of_cls.write_stats_data_ids_to_file.__doc__} => 行いますか？"):
                # 取得方法は非同期のみ
                obj_of_cls.lst_of_get_type = list(list(obj_of_cls.dct_of_get_type.items())[0])
                # 統計表IDをテキストファイルに書き出す
                await obj_of_cls.write_stats_data_ids_to_file()
            obj_of_cls.STATS_DATA_ID = obj_with_cui._input_stats_data_id()
            # 取得方法は同期のみ
            obj_of_cls.lst_of_get_type = list(list(obj_of_cls.dct_of_get_type.items())[1])
            obj_of_cls.get_table_from_api()
            obj_of_cls.lst_of_match_type = obj_with_cui._select_element(obj_of_cls.dct_of_match_type)
            if obj_with_cui._input_bool("フィルターをかけますか？"):
                obj_of_cls.lst_of_keyword = obj_with_cui._input_lst_of_text("抽出するキーワードを入力してください。")
                if len(obj_of_cls.lst_of_keyword) > 1:
                    obj_of_cls.lst_of_logic_type = obj_with_cui._select_element(obj_of_cls.dct_of_logic_type)
                obj_of_cls.df = obj_of_cls.filter_df(obj_of_cls.df)
            obj_of_cls.show_table()
            if obj_with_cui._input_bool(f"{obj_of_cls.output_table_to_csv.__doc__} => 行いますか？"):
                obj_of_cls.output_table_to_csv()
        except asyncio.CancelledError:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as e:
            obj_of_lt.logger.critical(f"***処理が失敗しました。***: \n{str(e)}")
        else:
            result = True
            obj_of_lt.logger.info("***処理が成功しました。***")
        finally:
            pass
        if obj_with_cui._input_bool("終了しますか？"):
            break
    return result


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        pass
    else:
        pass
    finally:
        pass
