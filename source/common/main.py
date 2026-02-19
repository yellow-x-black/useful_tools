import asyncio
import inspect
import sys


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
        print("\nUsage: ")
        usage_tpl: tuple = (
            "main.py => GUI Launcher",
            "main.py cui <tool_name> => CUI",
            "main.py gui <tool_name> => GUI",
        )
        print("\n".join(usage_tpl))
        print("\nTools List: ")
        tools_dct: dict = {
            "convert_libre_to_pdf": "cltp",
            "convert_office_to_pdf": "cotp",
            "convert_to_md": "ctm",
            "edit_pdf": "ep",
            "get_file_list": "gfl",
            "get_japan_government_statistics": "gjgs",
        }
        print("\n".join(f"{key} => {value}" for key, value in tools_dct.items()))
        print("\nAttention: ")
        attention_tpl: tuple = (
            "* If you execute with GUI mode on WSL2(Ubuntu), execute the following command.",
            "sudo apt install fonts-ipafont",
            "* If you input Japanese into a Linux GUI app on WSLg(Ubuntu), try the following steps:",
            "1. Execute the following command.",
            "sudo apt install ibus ibus-mozc",
            "2. Add the following to ~/.bashrc.",
            "ibus-daemon -drx",
            "export GTK_IM_MODULE=ibus",
            "export QT_IM_MODULE=ibus",
            "export XMODIFIERS=@im=ibus",
            "3. Execute the following command.",
            "ibus-setup",
            "4. Select the following on the opening window.",
            "Input Method => Add => Japanese => Mozc",
        )
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
