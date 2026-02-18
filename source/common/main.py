import asyncio
import inspect
import subprocess
import sys
from pathlib import Path


def main() -> bool:
    """Please select one from Useful Tools"""

    def run_with_cui(tool: str) -> bool:
        """CUIで実行します"""
        result: bool = False
        try:
            match tool:
                case "cltp":
                    from source.convert_libre_to_pdf.cltp_with_cui import main
                case "cotp":
                    from source.convert_office_to_pdf.cotp_with_cui import main
                case "ctm":
                    from source.convert_to_md.ctm_with_cui import main
                case "ep":
                    from source.edit_pdf.ep_with_cui import main
                case "gfl":
                    from source.get_file_list.gfl_with_cui import main
                case "gjgs":
                    from source.get_japan_government_statistics.gjgs_with_cui import main
                case _:
                    raise
            obj = main()
            if inspect.iscoroutine(obj):
                asyncio.run(obj)
            else:
                main()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def run_with_gui(tool: str) -> bool:
        """GUIで実行します"""
        result: bool = False
        try:
            match tool:
                case "cltp":
                    from source.convert_libre_to_pdf.cltp_with_gui import main
                case "cotp":
                    from source.convert_office_to_pdf.cotp_with_gui import main
                case "ctm":
                    from source.convert_to_md.ctm_with_gui import main
                case "ep":
                    from source.edit_pdf.ep_with_gui import main
                case "gfl":
                    from source.get_file_list.gfl_with_gui import main
                case "gjgs":
                    from source.get_japan_government_statistics.gjgs_with_gui import main
                case _:
                    raise
            main()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def run_gui_launcher() -> bool:
        """GUIランチャーを実行します"""
        result: bool = False
        try:
            from source.common.gui_launcher import main

            main()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception:
            raise
        else:
            result = True
        finally:
            pass
        return result

    def print_usage() -> None:
        """使用方法を表示します"""

        def get_git_root() -> Path:
            """gitリポジトリのルートディレクトリを取得します"""
            return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())

        def make_shortname_of_tools(name: str) -> str:
            """Toolsの短縮名を作成します"""
            return "".join(part[0] for part in name.split("_") if part)

        def get_dct_from_tools_dir(rel_path: str) -> dict:
            """sourceディレクトリからそれぞれのディレクトリ名と短縮名の辞書を取得します"""
            base_path = get_git_root() / rel_path
            # 除外するディレクトリ名
            EXCLUDE: list = ["__pycache__", "common"]
            return {p.name: make_shortname_of_tools(p.name) for p in base_path.iterdir() if p.is_dir() and p.name not in EXCLUDE}

        print("\nUsage: ")
        usage_tpl: tuple = (
            "main.py => GUI Launcher",
            "main.py cui <tool_name> => CUI",
            "main.py gui <tool_name> => GUI",
        )
        print("\n".join(usage_tpl))
        print("\nTools List: ")
        tools_dct: dict = get_dct_from_tools_dir("source")
        print("\n".join(f"{key} => {value}" for key, value in tools_dct.items()))
        print("\nAttention: ")
        attention_tpl: tuple = ("If you execute with GUI mode on WSL2(Ubuntu), execute the following command.", "sudo apt install fonts-ipafont")
        print("\n".join(attention_tpl))

    result: bool = False
    try:
        if len(sys.argv) == 1:
            run_gui_launcher()
        elif len(sys.argv) == 3:
            mode: str = sys.argv[1]
            tool: str = sys.argv[2]
            match mode:
                case "cui":
                    run_with_cui(tool)
                case "gui":
                    run_with_gui(tool)
                case _:
                    raise
        else:
            print_usage()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"***{main.__doc__} => 失敗しました。***: \n{str(e)}")
    else:
        result = True
    finally:
        pass
    return result


if __name__ == "__main__":
    main()
