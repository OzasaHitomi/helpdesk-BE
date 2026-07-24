from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from helpdesk_be.models.ticket import Ticket
from helpdesk_be.store.enum.user_role_type import UserRoleType
from tests.conftest import RollbackTracker
from tests.factories.auth_factory import create_user_and_login

# ====================================================================
# POST /tickets
# ====================================================================

# リクエストの形式
# POST → リクエストボディ（json）でtitle/detail/visibility(任意)を送る
# レスポンスの形式
# 201 → 登録成功（登録されたチケットのid/titleを返す）
# 403 → 社員以外のロールでログイン中
# 422 → title/detailが未入力・空欄
# 500 → DB登録処理自体が失敗（コミットエラー）
#
# 未ログイン時の401はget_current_user依存関数自体の挙動（tests/core/dependencies/test_auth.pyで単体テスト済み）
# のため、ここでは重複してテストしない


# 正常系のテスト（社員が公開設定を指定してチケットを登録すると201、DBに保存され、ステータスは新規質問になる）
def test_create_ticket_success(client: TestClient, db_session: Session) -> None:
    user = create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post(
        "/api/v1/tickets",
        json={
            "title": "ログインできない",
            "detail": "パスワードを変更したらログインできなくなりました",
            "visibility": "public",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "ログインできない"

    ticket = db_session.execute(select(Ticket).where(Ticket.id == data["id"])).scalar_one()
    assert ticket.title == "ログインできない"
    assert ticket.detail == "パスワードを変更したらログインできなくなりました"
    assert ticket.visibility.value == "public"
    assert ticket.status.value == "new_question"
    assert ticket.created_by_user_id == user.id


# ------------------------


# 正常系のテスト（公開設定を省略した場合は非公開として保存される）
def test_create_ticket_defaults_to_private_visibility(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post(
        "/api/v1/tickets",
        json={"title": "要件", "detail": "詳細"},
    )

    assert response.status_code == 201
    data = response.json()

    ticket = db_session.execute(select(Ticket).where(Ticket.id == data["id"])).scalar_one()
    assert ticket.visibility.value == "private"


# ------------------------

# 準正常系のテスト
# 社員以外のロールでは登録処理を実行できない


# サポートロールの場合は403
def test_create_ticket_with_support_role_returns_403(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.SUPPORT)

    response = client.post(
        "/api/v1/tickets",
        json={"title": "要件", "detail": "詳細"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "社員アカウントのみチケットを作成できます"


# ------------------------


# 管理者ロールの場合も403
def test_create_ticket_with_admin_role_returns_403(client: TestClient, db_session: Session) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)

    response = client.post(
        "/api/v1/tickets",
        json={"title": "要件", "detail": "詳細"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "社員アカウントのみチケットを作成できます"


# ------------------------

# 異常系のテスト
# 必須項目（title/detail）が空欄のまま送信された場合は登録を受け付けない


# titleが無い場合は422
def test_create_ticket_without_title_returns_422(client: TestClient, db_session: Session) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post("/api/v1/tickets", json={"detail": "詳細"})

    assert response.status_code == 422


# ------------------------


# titleが空白のみの場合も422
def test_create_ticket_with_blank_title_returns_422(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post("/api/v1/tickets", json={"title": "   ", "detail": "詳細"})

    assert response.status_code == 422


# ------------------------


# detailが無い場合は422
def test_create_ticket_without_detail_returns_422(client: TestClient, db_session: Session) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post("/api/v1/tickets", json={"title": "要件"})

    assert response.status_code == 422


# ------------------------


# detailが空白のみの場合も422
def test_create_ticket_with_blank_detail_returns_422(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post("/api/v1/tickets", json={"title": "要件", "detail": "   "})

    assert response.status_code == 422


# ------------------------

# 異常系のテスト
# DBへのコミット自体が失敗した場合はrollbackされ、500が返る


def test_create_ticket_with_commit_error(
    db_session: Session,
    client_with_commit_error: TestClient,
    rollback_tracker: RollbackTracker,
) -> None:
    create_user_and_login(db_session, client_with_commit_error, role=UserRoleType.EMPLOYEE)

    response = client_with_commit_error.post(
        "/api/v1/tickets",
        json={"title": "要件", "detail": "詳細"},
    )

    assert response.status_code == 500
    assert rollback_tracker.called is True
