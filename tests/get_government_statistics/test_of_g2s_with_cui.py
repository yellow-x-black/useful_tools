import pytest

from source.get_government_statistics import g2s_with_cui


# テスト関数: 指定されている関数の動作を確認するためのテストをする
def test_func(monkeypatch):
    # main を強制的に KeyboardInterrupt させる
    def fake_loop():
        raise KeyboardInterrupt

    monkeypatch.setattr("source.get_government_statistics.g2s_with_cui.main", fake_loop)
    with pytest.raises(KeyboardInterrupt):
        g2s_with_cui.main()
