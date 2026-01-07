import asyncio
import inspect
import sys


def main() -> bool:
    """Please select one from Useful Tools"""
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
            case "gfl":
                from source.get_file_list.gfl_with_cui import main
            case "g2s":
                from source.get_government_statistics.g2s_with_cui import main
            case "pt":
                from source.pdf_tools.pt_with_cui import main
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
            case "gfl":
                from source.get_file_list.gfl_with_gui import main
            case "g2s":
                from source.get_government_statistics.g2s_with_gui import main
            case "pt":
                from source.pdf_tools.pt_with_gui import main
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


def print_usage():
    """使用方法を表示します"""
    print(
        "usage: ",
        "main.py => GUI Launcher",
        "main.py cui <tool_name> => CUI",
        "main.py gui <tool_name> => GUI",
        sep="\n",
    )


if __name__ == "__main__":
    main()
