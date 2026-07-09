import pytest

from helpdesk_be.core.dependencies.database import get_db

# ------------------------------------------------------------------

# get_db: DBセッションをyieldし、正常終了時・例外発生時のどちらでも
# finallyでsession.close()を呼び出すジェネレータ


# 正常系のテスト（処理が正常終了した場合でもsession.close()が呼ばれる）
def test_get_db_closes_session_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    generator = get_db()
    session = next(generator)

    closed = {"called": False}
    original_close = session.close

    def fake_close() -> None:
        closed["called"] = True
        original_close()

    monkeypatch.setattr(session, "close", fake_close)

    # ジェネレータを最後まで進める（呼び出し元のwithブロックを抜ける動作に相当）
    with pytest.raises(StopIteration):
        next(generator)

    assert closed["called"] is True


# ------------------------


# 異常系のテスト（処理中に例外が発生した場合でもsession.close()が呼ばれる）
def test_get_db_closes_session_when_exception_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    generator = get_db()
    session = next(generator)

    closed = {"called": False}
    original_close = session.close

    def fake_close() -> None:
        closed["called"] = True
        original_close()

    monkeypatch.setattr(session, "close", fake_close)

    # 呼び出し元（例: リクエスト処理中）で例外が発生した想定
    with pytest.raises(ValueError, match="some error"):
        generator.throw(ValueError("some error"))

    assert closed["called"] is True
