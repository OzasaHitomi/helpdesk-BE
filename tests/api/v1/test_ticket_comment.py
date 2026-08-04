import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType
from helpdesk_be.store.enum.user_role_type import UserRoleType
from tests.factories.auth_factory import create_user_and_login
from tests.factories.ticket_comment_factory import create_ticket_comment
from tests.factories.ticket_factory import create_ticket
from tests.factories.user_factory import create_user

# ====================================================================
# GET /tickets/{ticket_id}/comments
# ====================================================================

# リクエストの形式
# GET → パスパラメータでticket_idを指定する
# レスポンスの形式
# 200 → 対応履歴一覧(投稿日時の降順。id/content/commenterName/createdAt)を返す
#        システムが自動登録した履歴(created_by_user_id=NULL)のcommenterNameは"system"になる
# 404 → 対象のチケットが存在しない、または閲覧権限がない場合(存在有無を推測させないため統一)
#
# 未ログイン時の401はget_current_user依存関数自体の挙動（tests/core/dependencies/test_auth.pyで単体テスト済み）
# のため、ここでは重複してテストしない


# 対応履歴が複数件あるとき、投稿日時の降順(新しいものが先頭)で返り、各要素に投稿者本人の名前が正しく入っている
# (質問者・サポート担当という別々のユーザーが投稿したコメントが混在する状況で確認する)
def test_list_ticket_comments_returns_items_ordered_by_created_at_desc(
    client: TestClient, db_session: Session
) -> None:
    questioner = create_user_and_login(
        db_session, client, name="質問太郎", role=UserRoleType.EMPLOYEE
    )
    support_user = create_user(
        db_session, name="担当花子", email="support@example.com", role=UserRoleType.SUPPORT
    )
    ticket = create_ticket(db_session, created_by_user_id=questioner.id)
    comment1 = create_ticket_comment(
        db_session,
        ticket_id=ticket.id,
        created_by_user_id=questioner.id,
        content="追加で質問があります",
    )
    comment2 = create_ticket_comment(
        db_session,
        ticket_id=ticket.id,
        created_by_user_id=support_user.id,
        content="ご確認ありがとうございます",
    )

    response = client.get(f"/api/v1/tickets/{ticket.id}/comments")

    assert response.status_code == 200
    data = response.json()
    # 新しい順(降順)で返るため、後に投稿した担当花子のコメントが先頭になる
    contents = [item["content"] for item in data]
    assert contents == [comment2.content, comment1.content]
    # 各要素の投稿者名が、その行を実際に投稿した本人と一致していること
    # (チケットの現在の担当者名ではなく、行ごとの投稿者名であることの確認)
    commenter_names = [item["commenterName"] for item in data]
    assert commenter_names == [support_user.name, questioner.name]
    assert data[0]["id"] == comment2.id
    assert "createdAt" in data[0]


# ------------------------


# 対応履歴が1件も無い場合は空配列が返る
def test_list_ticket_comments_returns_empty_items_when_no_comments_exist(
    client: TestClient, db_session: Session
) -> None:
    user = create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)
    ticket = create_ticket(db_session, created_by_user_id=user.id)

    response = client.get(f"/api/v1/tickets/{ticket.id}/comments")

    assert response.status_code == 200
    assert response.json() == []


# ------------------------

# 準正常系のテスト
# 閲覧権限がある場合は取得でき、無い場合は404になる(チケット詳細と同一ルール)


# 公開チケットは第三者の社員でも取得でき、コメントの投稿者名は閲覧者ではなく実際の投稿者(社員A)のまま返る
def test_list_ticket_comments_on_other_users_public_ticket_returns_200(
    client: TestClient, db_session: Session
) -> None:
    creator = create_user(db_session, name="社員A", email="employee_a@example.com")
    ticket = create_ticket(
        db_session, created_by_user_id=creator.id, visibility=TicketVisibilityType.PUBLIC
    )
    create_ticket_comment(db_session, ticket_id=ticket.id, created_by_user_id=creator.id)
    # ログインするのはコメントを投稿した社員Aとは別人(第三者)の社員B
    create_user_and_login(
        db_session, client, name="社員B", email="employee_b@example.com", role=UserRoleType.EMPLOYEE
    )

    response = client.get(f"/api/v1/tickets/{ticket.id}/comments")

    assert response.status_code == 200
    assert response.json()[0]["commenterName"] == creator.name


# ------------------------


# 自分の非公開チケットは質問者本人が取得できる
def test_list_ticket_comments_on_own_private_ticket_returns_200(
    client: TestClient, db_session: Session
) -> None:
    user = create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)
    ticket = create_ticket(
        db_session, created_by_user_id=user.id, visibility=TicketVisibilityType.PRIVATE
    )
    create_ticket_comment(db_session, ticket_id=ticket.id, created_by_user_id=user.id)

    response = client.get(f"/api/v1/tickets/{ticket.id}/comments")

    assert response.status_code == 200


# ------------------------


# 非公開チケットでもSUPPORT/ADMINは取得できる
@pytest.mark.parametrize(
    ("login_role"),
    [
        pytest.param(UserRoleType.SUPPORT, id="support"),
        pytest.param(UserRoleType.ADMIN, id="admin"),
    ],
)
def test_list_ticket_comments_on_private_ticket_is_viewable_by_support_or_admin(
    client: TestClient,
    db_session: Session,
    login_role: UserRoleType,
) -> None:
    creator = create_user(db_session, name="社員A", email="employee_a@example.com")
    ticket = create_ticket(
        db_session, created_by_user_id=creator.id, visibility=TicketVisibilityType.PRIVATE
    )
    create_ticket_comment(db_session, ticket_id=ticket.id, created_by_user_id=creator.id)
    # ログインするのはコメントを投稿した社員Aとは別人(第三者)
    create_user_and_login(
        db_session, client, name="担当花子", email="support@example.com", role=login_role
    )

    response = client.get(f"/api/v1/tickets/{ticket.id}/comments")

    assert response.status_code == 200
    assert response.json()[0]["commenterName"] == creator.name


# ------------------------


# 第三者の社員は、他人の非公開チケットの対応履歴を取得できない
def test_list_ticket_comments_on_other_users_private_ticket_returns_404(
    client: TestClient, db_session: Session
) -> None:
    creator = create_user(db_session, name="社員A", email="employee_a@example.com")
    ticket = create_ticket(
        db_session, created_by_user_id=creator.id, visibility=TicketVisibilityType.PRIVATE
    )
    create_ticket_comment(db_session, ticket_id=ticket.id, created_by_user_id=creator.id)
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.get(f"/api/v1/tickets/{ticket.id}/comments")

    assert response.status_code == 404


# ------------------------


# 投稿者がいない対応履歴(担当者割り当て等でシステムが自動登録したもの)は、対応者名が"system"と表示される
def test_list_ticket_comments_returns_system_as_commenter_name_for_system_comment(
    client: TestClient, db_session: Session
) -> None:
    user = create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)
    ticket = create_ticket(db_session, created_by_user_id=user.id)
    # created_by_user_idを渡さない(NULL) = システムが自動登録した履歴
    create_ticket_comment(
        db_session,
        ticket_id=ticket.id,
        content="担当者 担当花子 を担当に割り当てました",
    )

    response = client.get(f"/api/v1/tickets/{ticket.id}/comments")

    assert response.status_code == 200
    assert response.json()[0]["commenterName"] == "system"


# ------------------------


# 投稿者がいる通常の対応履歴(利用者・サポート担当の投稿)は、従来どおり投稿者名が表示される
def test_list_ticket_comments_returns_commenter_name_for_user_comment(
    client: TestClient, db_session: Session
) -> None:
    user = create_user_and_login(db_session, client, name="質問太郎", role=UserRoleType.EMPLOYEE)
    ticket = create_ticket(db_session, created_by_user_id=user.id)
    create_ticket_comment(db_session, ticket_id=ticket.id, created_by_user_id=user.id)

    response = client.get(f"/api/v1/tickets/{ticket.id}/comments")

    assert response.status_code == 200
    assert response.json()[0]["commenterName"] == user.name


# ------------------------


# 存在しないticket_idを指定した場合は404
def test_list_ticket_comments_with_nonexistent_ticket_returns_404(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.get("/api/v1/tickets/9999/comments")

    assert response.status_code == 404
