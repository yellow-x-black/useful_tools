import pytest

from source.convert_libre_to_pdf import cltp_with_cui


# テスト関数: 指定されている関数の動作を確認するためのテストをする
def test_func(monkeypatch):
    # main を強制的に KeyboardInterrupt させる
    def fake_loop():
        raise KeyboardInterrupt

    monkeypatch.setattr("source.convert_libre_to_pdf.cltp_with_cui.main", fake_loop)
    with pytest.raises(KeyboardInterrupt):
        cltp_with_cui.main()
