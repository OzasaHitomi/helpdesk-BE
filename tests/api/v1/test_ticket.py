from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from helpdesk_be.models.ticket import Ticket
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType
from helpdesk_be.store.enum.user_role_type import UserRoleType
from tests.conftest import RollbackTracker
from tests.factories.auth_factory import create_user_and_login
from tests.factories.ticket_factory import create_ticket
from tests.factories.user_factory import create_user

# ====================================================================
# POST /tickets
# ====================================================================

# リクエストの形式
# POST → リクエストボディ（json）でtitle/detail/visibility(すべて必須)を送る
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

# 準正常系のテスト
# 社員以外のロールでは登録処理を実行できない


# サポートロールの場合は403
def test_create_ticket_with_support_role_returns_403(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.SUPPORT)

    response = client.post(
        "/api/v1/tickets",
        json={"title": "要件", "detail": "詳細", "visibility": "public"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "社員アカウントのみチケットを作成できます"


# ------------------------


# 管理者ロールの場合も403
def test_create_ticket_with_admin_role_returns_403(client: TestClient, db_session: Session) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)

    response = client.post(
        "/api/v1/tickets",
        json={"title": "要件", "detail": "詳細", "visibility": "public"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "社員アカウントのみチケットを作成できます"


# ------------------------

# 異常系のテスト
# 必須項目（title/detail）が空欄のまま送信された場合は登録を受け付けない


# titleが無い場合は422
def test_create_ticket_without_title_returns_422(client: TestClient, db_session: Session) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post("/api/v1/tickets", json={"detail": "詳細", "visibility": "public"})

    assert response.status_code == 422
    assert response.json()["detail"] == [{"loc": ["body", "title"], "type": "missing"}]


# ------------------------


# titleが空文字列の場合も422
def test_create_ticket_with_empty_title_returns_422(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post(
        "/api/v1/tickets", json={"title": "", "detail": "詳細", "visibility": "public"}
    )

    assert response.status_code == 422
    assert response.json()["detail"] == [{"loc": ["body", "title"], "type": "string_too_short"}]


# ------------------------


# titleが空白のみの場合も422
def test_create_ticket_with_blank_title_returns_422(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post(
        "/api/v1/tickets", json={"title": "   ", "detail": "詳細", "visibility": "public"}
    )

    assert response.status_code == 422
    assert response.json()["detail"] == [{"loc": ["body", "title"], "type": "string_too_short"}]


# ------------------------


# detailが無い場合は422
def test_create_ticket_without_detail_returns_422(client: TestClient, db_session: Session) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post("/api/v1/tickets", json={"title": "要件", "visibility": "public"})

    assert response.status_code == 422
    assert response.json()["detail"] == [{"loc": ["body", "detail"], "type": "missing"}]


# ------------------------


# detailが空文字列の場合も422
def test_create_ticket_with_empty_detail_returns_422(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post(
        "/api/v1/tickets", json={"title": "要件", "detail": "", "visibility": "public"}
    )

    assert response.status_code == 422
    assert response.json()["detail"] == [{"loc": ["body", "detail"], "type": "string_too_short"}]


# ------------------------


# detailが空白のみの場合も422
def test_create_ticket_with_blank_detail_returns_422(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post(
        "/api/v1/tickets", json={"title": "要件", "detail": "   ", "visibility": "public"}
    )

    assert response.status_code == 422
    assert response.json()["detail"] == [{"loc": ["body", "detail"], "type": "string_too_short"}]


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
        json={"title": "要件", "detail": "詳細", "visibility": "public"},
    )

    assert response.status_code == 500
    assert rollback_tracker.called is True


# ====================================================================
# GET /tickets
# ====================================================================

# リクエストの形式
# GET → パラメータなし。ログイン中のユーザーのロールのみでフィルタ内容を決定する
# レスポンスの形式
# 200 → 質問日(created_at)降順のチケット一覧(質問者名・担当者名を含む)を返す
#
# 未ログイン時の401はget_current_user依存関数自体の挙動（tests/core/dependencies/test_auth.pyで単体テスト済み）
# のため、ここでは重複してテストしない


# チケットが1件も無い場合は空配列が返る
def test_list_tickets_returns_empty_items_when_no_tickets_exist(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.get("/api/v1/tickets")

    assert response.status_code == 200
    assert response.json() == []


# ------------------------


# 質問日(created_at)が新しい順に返る
def test_list_tickets_orders_by_created_at_desc(client: TestClient, db_session: Session) -> None:
    user = create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)
    create_ticket(
        db_session,
        created_by_user_id=user.id,
        title="古い質問",
        created_at=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Tokyo")),
    )
    create_ticket(
        db_session,
        created_by_user_id=user.id,
        title="新しい質問",
        created_at=datetime(2026, 7, 1, tzinfo=ZoneInfo("Asia/Tokyo")),
    )

    response = client.get("/api/v1/tickets")

    titles = [item["title"] for item in response.json()]
    assert titles == ["新しい質問", "古い質問"]


# ------------------------

# 準正常系のテスト
# 社員ロールでは、自分の非公開質問・他人の公開質問は表示され、他人の非公開質問だけが除外される


def test_list_tickets_with_employee_role_hides_other_users_private_tickets(
    client: TestClient, db_session: Session
) -> None:
    me = create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)
    other = create_user(db_session, name="他人", email="other@example.com")

    create_ticket(
        db_session,
        created_by_user_id=me.id,
        visibility=TicketVisibilityType.PRIVATE,
        title="自分の非公開",
    )
    create_ticket(
        db_session,
        created_by_user_id=other.id,
        visibility=TicketVisibilityType.PUBLIC,
        title="他人の公開",
    )
    create_ticket(
        db_session,
        created_by_user_id=other.id,
        visibility=TicketVisibilityType.PRIVATE,
        title="他人の非公開",
    )

    response = client.get("/api/v1/tickets")

    titles = {item["title"] for item in response.json()}
    assert titles == {"自分の非公開", "他人の公開"}


# ------------------------

# サポートロールでは、他人の非公開質問も含め全件表示される


def test_list_tickets_with_support_role_shows_all_tickets(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.SUPPORT)
    other = create_user(db_session, name="他人", email="other@example.com")
    create_ticket(
        db_session,
        created_by_user_id=other.id,
        visibility=TicketVisibilityType.PRIVATE,
        title="他人の非公開",
    )

    response = client.get("/api/v1/tickets")

    titles = {item["title"] for item in response.json()}
    assert titles == {"他人の非公開"}


# ------------------------

# 管理者ロールでも、他人の非公開質問も含め全件表示される


def test_list_tickets_with_admin_role_shows_all_tickets(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)
    other = create_user(db_session, name="他人", email="other@example.com")
    create_ticket(
        db_session,
        created_by_user_id=other.id,
        visibility=TicketVisibilityType.PRIVATE,
        title="他人の非公開",
    )

    response = client.get("/api/v1/tickets")

    titles = {item["title"] for item in response.json()}
    assert titles == {"他人の非公開"}


# ------------------------

# 質問者名・担当者名が先読み結果としてレスポンスに含まれる


def test_list_tickets_includes_questioner_and_support_user_names(
    client: TestClient, db_session: Session
) -> None:
    questioner = create_user_and_login(
        db_session, client, name="質問太郎", role=UserRoleType.EMPLOYEE
    )
    support_user = create_user(
        db_session, name="担当花子", email="support@example.com", role=UserRoleType.SUPPORT
    )
    create_ticket(
        db_session,
        created_by_user_id=questioner.id,
        support_user_id=support_user.id,
        title="対応中の質問",
    )

    response = client.get("/api/v1/tickets")

    item = response.json()[0]
    assert item["questionerName"] == "質問太郎"
    assert item["supportUserName"] == "担当花子"


# ------------------------

# 担当者が未割当てのチケットはsupportUserNameがnullで返る


def test_list_tickets_returns_null_support_user_name_when_unassigned(
    client: TestClient, db_session: Session
) -> None:
    user = create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)
    create_ticket(db_session, created_by_user_id=user.id, title="未担当の質問")

    response = client.get("/api/v1/tickets")

    item = response.json()[0]
    assert item["supportUserName"] is None
