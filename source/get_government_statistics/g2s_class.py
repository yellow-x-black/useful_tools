import asyncio
import csv
import io
import json
import shutil
import sys
from logging import Logger
from pathlib import Path
from typing import Any, AsyncGenerator
from xml.etree import ElementTree

import clipboard
import httpx
import pandas
from pandas import DataFrame
from tabulate import tabulate

from source.common.common import DatetimeTools


class GetGovernmentStatistics:
    """政府の統計データを取得します"""

    def __init__(self, logger: Logger):
        """初期化します"""
        self.log: Logger = logger
        self.log.info(self.__class__.__doc__)
        self.obj_of_dt2: DatetimeTools = DatetimeTools()
        self.credit_text: str = (
            "クレジット表示\n"
            "このサービスは、政府統計総合窓口(e-Stat)のAPI機能を使用していますが、"
            "サービスの内容は国によって保証されたものではありません。"
        )
        self.log.info(self.credit_text)
        # 統計表IDの一覧を取得する方法
        self.dct_of_get_type: dict = {
            "非同期": "処理の実行中に待ち時間が発生しても、次の処理に進める方法",
            "同期": "処理の実行中に待ち時間が発生しても、その処理の完了まで次に進まない方法",
        }
        # 取得するデータ形式
        self.dct_of_data_type: dict = {
            "xml": "タグ構造のデータ",
            "json": "キーと値のペアのデータ",
            "csv": "カンマ区切りのデータ",
        }
        # 検索方法
        self.dct_of_match_type: dict = {
            "検索しない": "なし",
            "部分一致": "フィールドの値にキーワードが含まれている",
            "完全一致": "フィールドの値がキーワードと完全に一致している",
        }
        # 抽出方法(2つ以上のキーワードがある場合)
        self.dct_of_logic_type: dict = {
            "OR抽出": "複数のキーワードのいずれかが含まれている",
            "AND抽出": "複数のキーワードの全てが含まれている",
        }
        # list変数のキー番号
        self.KEY: int = 0
        # list変数の説明番号
        self.DESCRIPTION: int = 1
        # 統計表IDの一覧を取得する方法
        self.lst_of_get_type: list = []
        # 取得するデータ形式
        self.lst_of_data_type: list = []
        # 検索方法
        self.lst_of_match_type: list = []
        # 抽出するキーワード
        self.lst_of_keyword: list = []
        # 抽出方法
        self.lst_of_logic_type: list = []
        # 統計表IDの一覧のCSVファイルのヘッダー
        self.header_of_ids_l: list = ["統計表ID", "統計名", "表題"]
        self.header_of_ids_s: str = ",".join(self.header_of_ids_l)
        # APIのバージョン
        self.VERSION: float = 3.0
        # アプリケーションID
        self.APP_ID: str = ""
        # 統計表ID
        self.STATS_DATA_ID: str = ""
        # 統計名
        self.STAT_NAME: str = ""
        # 表題
        self.TITLE: str = ""
        # dataframeの件数
        self.DATA_COUNT: int = 0
        # 指定の統計表のデータフレーム
        self.df: DataFrame = None
        # 処理をキャンセルするかどうか
        self.cancel: bool = False
        # exe化されている場合とそれ以外を切り分ける
        exe_path: Path = Path(sys.executable) if getattr(sys, "frozen", False) else Path(__file__)
        # 統計表IDの一覧のCSVファイルを格納するフォルダ
        self.folder_p_of_ids: Path = exe_path.parent / "__stats_data_ids__"
        self.folder_s_of_ids: str = str(self.folder_p_of_ids)
        self.log.info(f"統計表IDのリストを格納するフォルダ => {self.folder_s_of_ids}")
        # 指定の統計表のCSVファイルを格納するフォルダ
        self.folder_p_of_table: Path = exe_path.parent / "__output__"
        self.folder_s_of_table: str = str(self.folder_p_of_table)
        self.log.info(f"指定の統計表を格納するフォルダ => {self.folder_s_of_table}")

    def _parser_xml(self, res: httpx.Response) -> tuple[dict, int]:
        """XMLのデータを解析します(同期版と非同期版で共通)"""
        page_dct: dict = {}
        try:
            root: ElementTree.Element[str] = ElementTree.fromstring(res.text)
            table_lst: list[ElementTree.Element[str]] = root.findall(".//TABLE_INF")
            for t in table_lst:
                stat_id: str = (t.attrib.get("id", "") or "") if t is not None else ""
                element_of_stat_name: ElementTree.Element | None = t.find("STAT_NAME")
                stat_name: str = (element_of_stat_name.text or "") if element_of_stat_name is not None else ""
                element_of_title: ElementTree.Element | None = t.find("TITLE")
                title: str = (element_of_title.text or "") if element_of_title is not None else ""
                page_dct[stat_id] = {"stat_name": stat_name, "title": title}
        except asyncio.CancelledError:
            raise
        except KeyboardInterrupt:
            raise
        except Exception:
            # デバッグ用(加工前のデータをクリップボードにコピーする)
            clipboard.copy(res.text)
            raise
        else:
            pass
        finally:
            pass
        return page_dct, len(table_lst)

    def _parser_json(self, res: httpx.Response) -> tuple[dict, int]:
        """JSONのデータを解析します(同期版と非同期版で共通)"""
        page_dct: dict = {}
        try:
            data: Any = res.json()
            table_data: Any = data["GET_STATS_LIST"]["DATALIST_INF"]["TABLE_INF"]
            table_lst = [table_data] if isinstance(table_data, dict) else table_data
            for t in table_lst:
                stat_id: str = t.get("@id", "")
                statistics_name: str = t.get("STATISTICS_NAME", {})
                title: str = t.get("TITLE", {})
                page_dct[stat_id] = {
                    "statistics_name": statistics_name,
                    "title": title,
                }
        except asyncio.CancelledError:
            raise
        except KeyboardInterrupt:
            raise
        except Exception:
            # デバッグ用(加工前のデータをクリップボードにコピーする)
            clipboard.copy(json.dumps(data, indent=4, ensure_ascii=False))
            raise
        else:
            pass
        finally:
            pass
        return page_dct, len(table_lst)

    def _parser_csv(self, res: httpx.Response) -> tuple[dict, int]:
        """CSVのデータを解析します(同期版と非同期版で共通)"""
        page_dct: dict = {}
        row_count: int = 0
        try:
            lines: list = res.text.splitlines()
            # ヘッダー行を探す
            start_idx: int = 0
            for i, line in enumerate(lines):
                if "STAT_INF" in line:
                    # 次の行
                    start_idx = i + 1
                    break
            if start_idx == 0:
                raise Exception("CSVファイルにヘッダー行が見つかりません。")
            csv_text: str = "\n".join(lines[start_idx:])
            reader: csv.DictReader[str] = csv.DictReader(io.StringIO(csv_text))
            for row in reader:
                row_count += 1
                stat_id: str = row.get("TABLE_INF", "")
                stat_name: str = row.get("STAT_NAME", "")
                title: str = row.get("TITLE", "")
                page_dct[stat_id] = {"stat_name": stat_name, "title": title}
        except asyncio.CancelledError:
            raise
        except KeyboardInterrupt:
            raise
        except Exception:
            # デバッグ用(加工前のデータをクリップボードにコピーする)
            clipboard.copy(res.text)
            raise
        else:
            pass
        finally:
            pass
        return page_dct, row_count

    async def _get_stats_data_ids_with_async(self) -> AsyncGenerator[dict, None]:
        """ページを取得します(非同期版)"""
        try:
            parser_map: dict = {
                "xml": self._parser_xml,
                "json": self._parser_json,
                "csv": self._parser_csv,
            }
            # 統計表IDの一覧のURL
            dct_of_ids_url: dict = {
                "xml": f"http://api.e-stat.go.jp/rest/{self.VERSION}/app/getStatsList",
                "json": f"http://api.e-stat.go.jp/rest/{self.VERSION}/app/json/getStatsList",
                "csv": f"http://api.e-stat.go.jp/rest/{self.VERSION}/app/getSimpleStatsList",
            }
            data_type: str = self.lst_of_data_type[self.KEY]
            parser: Any = parser_map.get(data_type)
            if not parser:
                raise Exception("データタイプが対応していません")
            url: str = dct_of_ids_url[data_type]
            start: int = 1
            limit: int = 100
            async with httpx.AsyncClient(timeout=120.0) as client:
                while True:
                    params: dict = {
                        "appId": self.APP_ID,
                        "lang": "J",
                        "limit": limit,
                        "startPosition": start,
                    }
                    res: httpx.Response = await client.get(url, params=params)
                    res.encoding = "utf-8"
                    res.raise_for_status()
                    page_dct, count = parser(res)
                    if count == 0:
                        break
                    yield page_dct
                    start += limit
        except asyncio.CancelledError:
            raise
        except httpx.HTTPStatusError:
            raise
        except httpx.RequestError:
            raise
        except Exception:
            raise
        else:
            pass
        finally:
            pass

    async def write_stats_data_ids_to_file(self, chunk_size: int = 100) -> bool:
        """統計表IDの一覧をCSVファイルに書き出す"""
        result: bool = False
        try:
            await self._write_stats_data_ids_to_file_with_async(chunk_size)
        except asyncio.CancelledError:
            raise
        except httpx.HTTPStatusError:
            raise
        except httpx.RequestError:
            raise
        except KeyboardInterrupt:
            raise
        except Exception:
            raise
        else:
            result = True
        finally:
            self.cancel = False
        return result

    def _common_process_for_writing_stats_data_ids_to_file(self, file_index: int, buffer: list) -> bool:
        """ファイルに書き出す処理(同期版と非同期版で共通)"""
        result: bool = False
        try:
            file_p_of_ids = self.folder_p_of_ids / f"list_of_stats_data_ids_{file_index}.csv"
            file_p_of_ids.write_text("\n".join(buffer), encoding="utf-8")
        except asyncio.CancelledError:
            raise
        except KeyboardInterrupt:
            raise
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    async def _write_stats_data_ids_to_file_with_async(self, chunk_size: int = 100) -> bool:
        """統計表IDの一覧をCSVファイルに書き出す(非同期版)"""
        result: bool = False
        try:
            self.log.info(f"{self._write_stats_data_ids_to_file_with_async.__doc__} => 処理中...")
            self.folder_p_of_ids.mkdir(parents=True, exist_ok=True)
            # フォルダの中を空にする
            for e in self.folder_p_of_ids.iterdir():
                if e.is_dir():
                    shutil.rmtree(e)
                else:
                    e.unlink()
            buffer: list = [self.header_of_ids_s]
            file_index: int = 1
            async for page in self._get_stats_data_ids_with_async():
                for stat_id, info in page.items():
                    col2: str = info.get("stat_name", info.get("statistics_name", ""))
                    col3: str = info.get("title", "")
                    if col3:
                        # データクレンジング
                        col3 = col3.replace("\u002c", "\u3001").replace("\uff0c", "\u3001")
                    buffer.append(f"{stat_id},{col2},{col3}")
                    if len(buffer) >= chunk_size:
                        self._common_process_for_writing_stats_data_ids_to_file(file_index, buffer)
                        buffer.clear()
                        buffer.append(self.header_of_ids_s)
                        file_index += 1
                if self.cancel:
                    break
            if len(buffer) > 1:
                self._common_process_for_writing_stats_data_ids_to_file(file_index, buffer)
        except asyncio.CancelledError:
            self.cancel = True
            raise
        except httpx.HTTPStatusError:
            raise
        except httpx.RequestError:
            raise
        except Exception:
            raise
        else:
            result = True
        finally:
            if self.cancel:
                self.log.warning(f"{self._write_stats_data_ids_to_file_with_async.__doc__} => 中止しました。")
            elif result:
                self.log.info(f"{self._write_stats_data_ids_to_file_with_async.__doc__} => 成功しました。")
            else:
                self.log.error(f"{self._write_stats_data_ids_to_file_with_async.__doc__} => 失敗しました。")
        return result

    def get_table_from_api(self) -> bool:
        """APIから指定の統計表を取得します"""

        def _get_params_of_url() -> dict:
            """APIのURLのパラメータを取得します"""
            params: dict = {
                "appId": self.APP_ID,  # アプリケーションID
                "statsDataId": self.STATS_DATA_ID,  # 統計表ID
                "lang": "J",  # 言語
                "limit": 100,
                "metaGetFlg": "Y",  # メタ情報の取得フラグ
                "cntGetFlg": "N",  # 件数の取得フラグ
                "explanationGetFlg": "N",  # 解説情報の有無フラグ
                "annotationGetFlg": "N",  # 注釈情報の有無フラグ
                "sectionHeaderFlg": 1,  # 見出し行の有無フラグ
                "replaceSpChars": 0,  # 特殊文字のエスケープフラグ
            }
            return params

        def _with_xml(client: httpx.Client, dct_of_params: dict) -> DataFrame:
            """XMLでデータを取得します"""
            try:
                id_url: str = f"http://api.e-stat.go.jp/rest/{self.VERSION}/app/getStatsData"
                # リクエストを送信する
                res: httpx.Response = client.get(id_url, params=dct_of_params)
                # 解析して、ルート要素を取得する
                root: ElementTree.Element[str] = ElementTree.fromstring(res.text)
                # CLASS_OBJからコードと名称のマッピングを作成する
                mapping: dict = {}
                for obj in root.findall(".//CLASS_OBJ"):
                    obj_id: str = obj.attrib["id"]
                    code_map: dict = {}
                    for cls in obj.findall("CLASS"):
                        # codeをキー、nameを値とする辞書を作成する
                        code_map[cls.attrib["code"]] = cls.attrib.get("name", cls.attrib["code"])
                    mapping[obj_id] = code_map
                # VALUEを取得し、行ごとの辞書に変換する
                rows: list = []
                for element in root.findall(".//VALUE"):
                    row: dict = {}
                    for key, value in element.attrib.items():
                        if key in mapping:
                            row[key] = mapping[key].get(value, value)
                        else:
                            row[key] = value
                    # VALUEのテキストを追加する
                    row["値"] = (element.text or "").strip()
                    rows.append(row)
                df: DataFrame = pandas.DataFrame(rows)
                # 列名を日本語に変換する
                id2name: dict = {}
                for obj in root.findall(".//CLASS_OBJ"):
                    obj_id: str = obj.attrib["id"]
                    obj_name: str = obj.attrib.get("name", obj_id)
                    id2name[obj_id] = obj_name
                id2name["unit"] = "単位"
                df.rename(columns=id2name, inplace=True)
                # 値列を数値型に変換する
                if "値" in df.columns:
                    df["値"] = pandas.to_numeric(df["値"], errors="coerce")
            except Exception:
                raise
            else:
                pass
            finally:
                # デバッグ用(加工前のデータをクリップボードにコピーする)
                clipboard.copy(res.text)
            return df

        def _with_json(client: httpx.Client, dct_of_params: dict) -> DataFrame:
            """JSONでデータを取得します"""
            try:
                id_url: str = f"http://api.e-stat.go.jp/rest/{self.VERSION}/app/json/getStatsData"
                # リクエストを送信する
                res: httpx.Response = client.get(id_url, params=dct_of_params)
                data: Any = res.json()
                # CLASS_OBJとVALUEを抽出する
                class_inf: Any = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["CLASS_INF"]["CLASS_OBJ"]
                values: Any = data["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
                # idと列名の対応表を作成する
                col_name_map: dict = {obj["@id"]: obj["@name"] for obj in class_inf}
                col_name_map["unit"] = "単位"
                # CLASS_OBJ内のコードを日本語名に置換する辞書を作成する
                code_to_name: dict = {}
                for obj in class_inf:
                    cid: str = obj["@id"]
                    cls: Any = obj["CLASS"]
                    if isinstance(cls, list):
                        code_to_name[cid] = {c["@code"]: c["@name"] for c in cls}
                    else:
                        code_to_name[cid] = {cls["@code"]: cls["@name"]}
                # VALUEの各行を日本語に変換する
                translated_rows: list = []
                for value in values:
                    row: dict = {}
                    for k, v in value.items():
                        jp_col: str = ""
                        if k.startswith("@") and k[1:] in code_to_name:
                            jp_col: Any = col_name_map.get(k[1:], k[1:])
                            row[jp_col] = code_to_name[k[1:]].get(v, v)
                        elif k == "@unit":
                            row["単位"] = v
                        elif k == "$":
                            row["値"] = v
                        else:
                            row[k] = v
                    translated_rows.append(row)
                df: DataFrame = pandas.DataFrame(translated_rows)
                # 値列を数値型に変換する
                if "値" in df.columns:
                    df["値"] = pandas.to_numeric(df["値"], errors="coerce")
            except Exception:
                raise
            else:
                pass
            finally:
                # デバッグ用(加工前のデータをクリップボードにコピーする)
                clipboard.copy(json.dumps(res.json(), indent=4, ensure_ascii=False))
            return df

        def _with_csv(client: httpx.Client, dct_of_params: dict) -> DataFrame:
            """CSVでデータを取得します"""
            try:
                id_url: str = f"http://api.e-stat.go.jp/rest/{self.VERSION}/app/getSimpleStatsData"
                # リクエストを送信する
                res: httpx.Response = client.get(id_url, params=dct_of_params)
                lines: list[str] = res.text.splitlines()
                # VALUE行の位置を検索する
                value_idx: int = 0
                for i, line in enumerate(lines):
                    if line.strip().replace('"', "") == "VALUE":
                        value_idx = i
                        break
                if value_idx == 0:
                    raise Exception("CSVに 'VALUE' 行が見つかりませんでした。")
                # ヘッダー行を取得する
                header_cols: list[str] = [h.strip('"') for h in lines[value_idx + 1].split(",")]
                # データ本体を文字列として抽出する
                csv_body: str = "\n".join(lines[value_idx + 2 :])
                df: DataFrame = pandas.read_csv(io.StringIO(csv_body), header=None)
                df.columns = header_cols
                # 列名を日本語に置換し、不要な英語コード列を削除する
                rename_map: dict = {}
                drop_cols: list = []
                i: int = 0
                while i < len(header_cols):
                    eng: str = header_cols[i]
                    if eng.endswith("_code") and i + 1 < len(header_cols):
                        # 英語コード列は削除する
                        drop_cols.append(eng)
                        i += 2
                        continue
                    # 単独列を処理する
                    elif eng == "unit":
                        rename_map[eng] = "単位"
                    elif eng == "value":
                        rename_map[eng] = "値"
                    else:
                        rename_map[eng] = eng
                    i += 1
                df = df.rename(columns=rename_map)
                df = df.drop(columns=drop_cols)
                # 値列を数値型に変換する
                if "値" in df.columns:
                    df["値"] = pandas.to_numeric(df["値"], errors="coerce")
            except Exception:
                raise
            else:
                pass
            finally:
                # デバッグ用(加工前のデータをクリップボードにコピーする)
                clipboard.copy(res.text)
            return df

        result: bool = False
        try:
            dct_of_params: dict = _get_params_of_url()
            # セッションを管理する
            with httpx.Client(timeout=120.0) as client:
                match self.lst_of_data_type[self.KEY]:
                    case "xml":
                        self.df = _with_xml(client, dct_of_params)
                    case "json":
                        self.df = _with_json(client, dct_of_params)
                    case "csv":
                        self.df = _with_csv(client, dct_of_params)
                    case _:
                        raise Exception("データタイプが対応していません。")
            self.DATA_COUNT = len(self.df)
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def filter_df(self, df: DataFrame) -> DataFrame:
        """データフレームをフィルターにかけます"""
        filtered_df: DataFrame | None = None
        try:
            match self.lst_of_match_type[self.KEY]:
                case "部分一致":
                    # 全列で部分一致検索する
                    if len(self.lst_of_keyword) == 1:
                        # 単一キーワード
                        kw: str = str(self.lst_of_keyword[0])
                        filtered_df = df[
                            df.apply(
                                lambda row: row.astype(str).str.contains(kw, case=False, na=False).any(),
                                axis=1,
                            )
                        ]
                    else:
                        # 複数キーワード
                        match self.lst_of_logic_type[self.KEY]:
                            case "OR抽出":
                                pattern: str = "|".join(map(str, self.lst_of_keyword))
                                filtered_df = df[
                                    df.apply(
                                        lambda row: row.astype(str).str.contains(pattern, case=False, na=False).any(),
                                        axis=1,
                                    )
                                ]
                            case "AND抽出":
                                filtered_df = df[
                                    df.apply(
                                        lambda row: all(row.astype(str).str.contains(k, case=False, na=False).any() for k in self.lst_of_keyword),
                                        axis=1,
                                    )
                                ]
                            case _:
                                raise Exception("その抽出方法はありません。")
                case "完全一致":
                    # 全列で完全一致検索する
                    if len(self.lst_of_keyword) == 1:
                        # 単一キーワード
                        kw: str = str(self.lst_of_keyword[0])
                        filtered_df = df[df.apply(lambda row: row.astype(str).eq(kw).any(), axis=1)]
                    else:
                        # 複数キーワード
                        match self.lst_of_logic_type[self.KEY]:
                            case "OR抽出":
                                filtered_df = df[
                                    df.apply(
                                        lambda row: row.astype(str).isin(self.lst_of_keyword).any(),
                                        axis=1,
                                    )
                                ]
                            case "AND抽出":
                                filtered_df = df[
                                    df.apply(
                                        lambda row: all(row.astype(str).eq(k).any() for k in self.lst_of_keyword),
                                        axis=1,
                                    )
                                ]
                            case _:
                                raise Exception("その抽出方法はありません。")
                case _:
                    raise Exception("その検索方法はありません。")
            self.DATA_COUNT = len(filtered_df)
        except Exception:
            raise
        else:
            pass
        finally:
            pass
        return filtered_df

    def show_table(self) -> bool:
        """指定の統計表を表示します"""
        result: bool = False
        try:
            self.log.info(tabulate(self.df, headers="keys", tablefmt="github", showindex=False))
            self.log.info(f"統計表ID => {self.STATS_DATA_ID}")
            self.log.info("データの取得形式 => " + ": ".join(self.lst_of_data_type))
            self.log.info("検索方法 => " + ": ".join(self.lst_of_match_type))
            self.log.info("抽出するキーワード => " + (", ".join(map(str, self.lst_of_keyword)) if self.lst_of_keyword else "なし"))
            self.log.info("抽出方法 => " + (": ".join(self.lst_of_logic_type) if self.lst_of_logic_type else "なし"))
            self.log.info(f"表示件数 => {self.DATA_COUNT}")
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def output_table_to_csv(self) -> bool:
        """指定の統計表をcsvファイルに出力します"""
        result: bool = False
        try:
            self.folder_p_of_table.mkdir(parents=True, exist_ok=True)
            file_p_of_table: Path = self.folder_p_of_table / f"stats_table_{self.STATS_DATA_ID}_{self.obj_of_dt2._convert_for_file_name()}.csv"
            file_s_of_table: str = str(file_p_of_table)
            self.df.to_csv(file_s_of_table, index=False, encoding="utf-8")
        except Exception:
            raise
        else:
            result = True
            self.log.info(f"指定の統計表のファイル => {file_s_of_table}")
        finally:
            pass
        return result
