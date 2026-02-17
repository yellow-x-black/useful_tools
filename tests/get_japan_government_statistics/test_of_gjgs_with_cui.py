import pytest

from source.get_japan_government_statistics import gjgs_with_cui


# テスト関数: 指定されている関数の動作を確認するためのテストをする
def test_func(monkeypatch):
    # main を強制的に KeyboardInterrupt させる
    def fake_loop():
        raise KeyboardInterrupt

    monkeypatch.setattr("source.get_japan_government_statistics.gjgs_with_cui.main", fake_loop)
    with pytest.raises(KeyboardInterrupt):
        gjgs_with_cui.main()
