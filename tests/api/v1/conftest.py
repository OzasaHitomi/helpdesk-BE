from collections.abc import Generator

import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.main import app


# 正常に動作するクライアントの作成
@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:

    def override_get_db() -> Generator[Session]:
        yield db_session

    # get_dbが呼ばれた時に、上のoverride_get_dbに上書きするようにする
    app.dependency_overrides[get_db] = override_get_db

    # クライアント作成
    client = TestClient(app, base_url="http://testserver.example")
    yield client
    # ↓20行めの上書きする仕様をリセット
    app.dependency_overrides.clear()


# 異常な場合のクライアント
@pytest.fixture
def client_with_commit_error(db_session_commit_error: Session) -> Generator[TestClient]:

    def override_get_db() -> Generator[Session]:
        yield db_session_commit_error

    # get_dbが呼ばれた時に、上のoverride_get_dbに上書きするようにする
    app.dependency_overrides[get_db] = override_get_db

    # クライアント作成
    # base_urlはclientフィクスチャと同じくドット入りホスト名にする必要がある
    # （ドット無しの"testserver"だとCookieのdomain照合がずれ、ログイン中でも401になってしまう）
    client = TestClient(app, base_url="http://testserver.example", raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()
