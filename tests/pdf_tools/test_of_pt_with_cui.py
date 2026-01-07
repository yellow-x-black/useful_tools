import pytest

from source.pdf_tools import pt_with_cui


# テスト関数: 指定されている関数の動作を確認するためのテストをする
def test_func(monkeypatch):
    # main を強制的に KeyboardInterrupt させる
    def fake_loop():
        raise KeyboardInterrupt

    monkeypatch.setattr("source.pdf_tools.pt_with_cui.main", fake_loop)
    with pytest.raises(KeyboardInterrupt):
        pt_with_cui.main()
