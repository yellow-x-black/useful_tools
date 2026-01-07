import pytest

from source.convert_to_md import ctm_with_cui


# テスト関数: 指定されている関数の動作を確認するためのテストをする
def test_func(monkeypatch):
    # main を強制的に KeyboardInterrupt させる
    def fake_loop():
        raise KeyboardInterrupt

    monkeypatch.setattr("source.convert_to_md.ctm_with_cui.main", fake_loop)
    with pytest.raises(KeyboardInterrupt):
        ctm_with_cui.main()
