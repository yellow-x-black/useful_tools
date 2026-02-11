import pytest

from source.common import main


# テスト関数: 指定されている関数の動作を確認するためのテストをする
def test_func(monkeypatch):
    # main を強制的に KeyboardInterrupt させる
    def fake_loop():
        raise KeyboardInterrupt

    monkeypatch.setattr("source.common.main.main", fake_loop)
    with pytest.raises(KeyboardInterrupt):
        main.main()
