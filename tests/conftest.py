from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

import pytest

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy import Connection, create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv(".env.test.unit", override=True)

from helpdesk_be.core.config.base import core_settings  # noqa: E402


@pytest.fixture(autouse=True, scope="session")
def apply_migrations() -> None:
    project_root = Path(__file__).resolve().parents[1]
    alembic_dir = project_root / "src" / "helpdesk_be"
    alembic_ini_path = alembic_dir / "alembic.ini"

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", core_settings.database_url)
    alembic_cfg.set_main_option("script_location", str(alembic_dir / "migrations"))

    command.upgrade(alembic_cfg, "head")


@pytest.fixture
def db_connection() -> Generator[Connection]:
    engine = create_engine(core_settings.database_url)
    connection = engine.connect()  # transactionに必要
    transaction = connection.begin()
    try:
        yield connection
    finally:
        if (
            transaction.is_active
        ):  # 異常系のテストでエラーが起きた場合、トランザクションが終了するためrollbackができない
            transaction.rollback()  # 流れの初期化
        connection.close()  # 流れ（transactionを）見るモード停止


@pytest.fixture
def db_session(db_connection: Connection) -> Generator[Session]:
    # session作成
    SessionTest = sessionmaker(bind=db_connection, autoflush=False, autocommit=False)
    session = SessionTest()
    try:
        yield session
    finally:
        session.close()


@dataclass
class RollbackTracker:
    # called　呼ばれたか呼ばれてないかのフラグ（自作したフラグ）
    called: bool = False


# クラスからインスタンスを作成する関数
@pytest.fixture
def rollback_tracker() -> RollbackTracker:
    return RollbackTracker()


# ----------------------------------------------------------------------------------------


# コミット時に例外を発生させるDBセッション
@pytest.fixture
def db_session_commit_error(
    db_connection: Connection,
    rollback_tracker: RollbackTracker,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Session]:
    testing_session = sessionmaker(bind=db_connection)
    session = testing_session()
    original_rollback = session.rollback

    def fake_commit() -> None:
        # session.commit()が呼ばれた瞬間に、Exception("Simulated commit error")が発生するようになる
        raise Exception("Simulated commit error")

    def fake_rollback() -> None:
        # フラグを立てる
        rollback_tracker.called = True
        # 本物のrollbackも実行する
        return original_rollback()

    monkeypatch.setattr(session, "commit", fake_commit)
    # commitが失敗したとき、rollbackが呼ばれるかをテストする
    monkeypatch.setattr(session, "rollback", fake_rollback)

    try:
        yield session
    finally:
        session.close()
