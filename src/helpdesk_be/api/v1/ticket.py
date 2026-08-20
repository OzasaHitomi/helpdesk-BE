from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.auth import get_current_user
from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.core.dependencies.permission import require_role
from helpdesk_be.core.dependencies.ticket import (
    get_ticket_or_404,
    require_own_assigned_ticket,
    require_ticket_status_editable,
    require_viewable_ticket,
)
from helpdesk_be.exceptions.business_exception import BusinessException
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.loggers.custom_logger import logger
from helpdesk_be.logic.business.ticket_status_display_name import get_ticket_status_display_name
from helpdesk_be.logic.business.ticket_status_transition import can_transition_ticket_status
from helpdesk_be.models.ticket import Ticket
from helpdesk_be.models.ticket_comment import TicketComment
from helpdesk_be.models.user import User
from helpdesk_be.repositories.ticket import get_tickets_with_users
from helpdesk_be.repositories.ticket_comment import get_comments_with_users_by_ticket_id
from helpdesk_be.schemas.request.v1.ticket import (
    CreateTicketRequest,
    UpdateTicketStatusRequest,
)
from helpdesk_be.schemas.request.v1.ticket_comment import CreateTicketCommentRequest
from helpdesk_be.schemas.response.v1.ticket import (
    AssignTicketResponse,
    CreateTicketResponse,
    GetTicketResponse,
    GetTicketsResponseItem,
    PublishTicketResponse,
    UnassignTicketResponse,
    UnpublishTicketResponse,
    UpdateTicketStatusResponse,
)
from helpdesk_be.schemas.response.v1.ticket_comment import (
    CreateTicketCommentResponse,
    GetTicketCommentsResponseItem,
)
from helpdesk_be.store.enum.ticket_status_type import TicketStatusType
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType
from helpdesk_be.store.enum.user_role_type import UserRoleType

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateTicketResponse,
    dependencies=[
        Depends(
            require_role(UserRoleType.EMPLOYEE, message="社員アカウントのみチケットを作成できます")
        )
    ],
)
def create_ticket(
    body: CreateTicketRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> CreateTicketResponse:
    new_ticket = Ticket(
        title=body.title,
        detail=body.detail,
        visibility=body.visibility,
        status=TicketStatusType.NEW_QUESTION,
        created_by_user_id=user.id,
    )
    session.add(new_ticket)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"failed to create ticket {e}")
        raise e

    return CreateTicketResponse(
        id=new_ticket.id,
        title=new_ticket.title,
        detail=new_ticket.detail,
        visibility=new_ticket.visibility,
        status=new_ticket.status,
        created_by_user_id=new_ticket.created_by_user_id,
        support_user_id=new_ticket.support_user_id,
    )


# ------------------------


@router.get("", response_model=list[GetTicketsResponseItem])
def list_tickets(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[GetTicketsResponseItem]:
    # SUPPORT/ADMINは全件、それ以外(将来ロールが増えた場合も含む)は「公開 または 自分が質問者」のみ閲覧可(fail-closed)
    # このルールはlogic/business/ticket_permission.pyのcan_view_ticketと同一(get_ticketではそちらを使用)
    if user.role in (UserRoleType.SUPPORT, UserRoleType.ADMIN):
        tickets = get_tickets_with_users(session)
    else:
        tickets = get_tickets_with_users(session, visible_to_user_id=user.id)

    return [
        GetTicketsResponseItem(
            id=ticket.id,
            title=ticket.title,
            visibility=ticket.visibility,
            status=ticket.status,
            questioner_name=ticket.questioner.name,
            support_user_name=ticket.support_user.name if ticket.support_user else None,
            created_at=ticket.created_at,
        )
        for ticket in tickets
    ]


# ------------------------


@router.get("/{ticket_id}", response_model=GetTicketResponse)
def get_ticket(
    ticket: Annotated[Ticket, Depends(require_viewable_ticket)],
) -> GetTicketResponse:
    return GetTicketResponse(
        id=ticket.id,
        title=ticket.title,
        detail=ticket.detail,
        visibility=ticket.visibility,
        status=ticket.status,
        created_by_user_id=ticket.created_by_user_id,
        support_user_id=ticket.support_user_id,
        support_user_name=ticket.support_user.name if ticket.support_user else None,
        created_at=ticket.created_at,
    )


# ------------------------


@router.get("/{ticket_id}/comments", response_model=list[GetTicketCommentsResponseItem])
def list_ticket_comments(
    ticket: Annotated[Ticket, Depends(require_viewable_ticket)],
    session: Annotated[Session, Depends(get_db)],
) -> list[GetTicketCommentsResponseItem]:
    comments = get_comments_with_users_by_ticket_id(session, ticket.id)

    # TicketCommentモデルのリストをレスポンススキーマへ変換する。
    # commenter_nameの表示ルール(system/管理者への匿名化)はcommenter_display_name()側を参照
    return [
        GetTicketCommentsResponseItem(
            id=comment.id,
            content=comment.content,
            commenter_name=comment.commenter_display_name(),
            created_at=comment.created_at,
        )
        for comment in comments
    ]


# ------------------------


@router.post(
    "/{ticket_id}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateTicketCommentResponse,
)
def create_ticket_comment(
    body: CreateTicketCommentRequest,
    ticket: Annotated[Ticket, Depends(require_viewable_ticket)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> CreateTicketCommentResponse:
    new_comment = TicketComment(
        ticket_id=ticket.id,
        content=body.content,
        created_by_user_id=user.id,
    )
    session.add(new_comment)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"failed to create ticket comment {e}")
        raise e

    return CreateTicketCommentResponse(
        id=new_comment.id,
        ticket_id=new_comment.ticket_id,
        content=new_comment.content,
        created_by_user_id=user.id,
        created_at=new_comment.created_at,
    )


# ------------------------


@router.put(
    "/{ticket_id}/assign",
    response_model=AssignTicketResponse,
    dependencies=[
        Depends(
            require_role(UserRoleType.SUPPORT, message="サポート担当のみこの操作を実行できます")
        )
    ],
)
def assign_ticket_to_self(
    ticket: Annotated[Ticket, Depends(get_ticket_or_404)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> AssignTicketResponse:
    # --- 状態チェック: すでに担当者が設定済み、またはステータスが新規質問以外の場合は
    #     現在の状態と矛盾する操作として422(BusinessException)を返す ---
    if ticket.support_user_id is not None:
        raise BusinessException("すでに担当者が設定されています")
    if ticket.status != TicketStatusType.NEW_QUESTION:
        raise BusinessException("新規質問以外のチケットには担当者を設定できません")

    # --- 更新処理: 担当者・ステータスを更新し、対応履歴にシステム履歴を追加する
    #     (Ticketの更新とTicketCommentの追加を同一トランザクションでコミットする) ---
    ticket.support_user_id = user.id
    ticket.status = TicketStatusType.ASSIGNED

    new_comment = TicketComment(
        ticket_id=ticket.id,
        content=f"担当者 {user.name} を担当に割り当てました",
        created_by_user_id=None,
    )
    session.add(new_comment)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"failed to assign ticket {e}")
        raise e

    # --- レスポンス構築 ---
    # support_user_idはticket.support_user_id(型はint | None)ではなくuser.id(型はint)を使う。
    # 直前でticket.support_user_id = user.idと代入済みで値は同じだが、
    # ticket.support_user_idは静的な型がint | Noneのままのため、int専用のAssignTicketResponseに渡すと型エラーになる
    return AssignTicketResponse(
        id=ticket.id,
        status=ticket.status,
        support_user_id=user.id,
        support_user_name=user.name,
        updated_at=ticket.updated_at,
    )


# ------------------------


@router.delete("/{ticket_id}/assign", response_model=UnassignTicketResponse)
def unassign_ticket(
    ticket: Annotated[Ticket, Depends(require_own_assigned_ticket)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> UnassignTicketResponse:
    # --- 状態チェック: 担当者割り当て済み・対応中以外のステータスは解除できない ---
    if ticket.status not in (TicketStatusType.ASSIGNED, TicketStatusType.IN_PROGRESS):
        raise BusinessException("このステータスのチケットは担当解除できません")

    # --- 更新処理: 担当者を外しステータスを新規質問に戻し、対応履歴にシステム履歴を追加する
    #     (Ticketの更新とTicketCommentの追加を同一トランザクションでコミットする) ---
    assignee_name = user.name  # support_user_idをクリアする前に退避する
    ticket.support_user_id = None
    ticket.status = TicketStatusType.NEW_QUESTION

    new_comment = TicketComment(
        ticket_id=ticket.id,
        content=f"担当者 {assignee_name} の担当を解除しました",
        created_by_user_id=None,
    )
    session.add(new_comment)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"failed to unassign ticket {e}")
        raise e

    return UnassignTicketResponse(
        id=ticket.id,
        status=ticket.status,
        support_user_id=ticket.support_user_id,
        support_user_name=None,
        updated_at=ticket.updated_at,
    )


# ------------------------


@router.put("/{ticket_id}/status", response_model=UpdateTicketStatusResponse)
def update_ticket_status(
    body: UpdateTicketStatusRequest,
    ticket: Annotated[Ticket, Depends(require_ticket_status_editable)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> UpdateTicketStatusResponse:
    # --- 状態チェック: 新規質問への/からの遷移は担当者割当て/解除(assign_ticket_to_self/unassign_ticket)の
    #     専任領域のためこのAPIでは扱わない。加えて、定義された遷移ルールに反する変更も422(BusinessException)を返す ---
    if TicketStatusType.NEW_QUESTION in (
        ticket.status,
        body.status,
    ) or not can_transition_ticket_status(ticket.status, body.status):
        raise BusinessException("このステータス変更はできません")

    # --- 更新処理: ステータスを更新し、対応履歴にシステム履歴を追加する
    #     (Ticketの更新とTicketCommentの追加を同一トランザクションでコミットする)
    #     表示用ステータス名はクライアントから受け取らず、BE側のマッピング(get_ticket_status_display_name)
    #     から求める(クライアント入力をそのまま履歴に埋め込むと任意文字列を残せてしまうため) ---
    ticket.status = body.status
    status_display_name = get_ticket_status_display_name(body.status)

    new_comment = TicketComment(
        ticket_id=ticket.id,
        content=f"ステータスを「{status_display_name}」に変更しました",
        created_by_user_id=user.id,
    )
    session.add(new_comment)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"failed to update ticket status {e}")
        raise e

    return UpdateTicketStatusResponse(
        id=ticket.id, status=ticket.status, updated_at=ticket.updated_at
    )


# ------------------------


# 非公開 → 公開
@router.put(
    "/{ticket_id}/publish",
    response_model=PublishTicketResponse,
    dependencies=[
        Depends(
            require_role(
                UserRoleType.ADMIN,
                UserRoleType.SUPPORT,
                message="サポート担当、または管理者のみ公開設定を変更できます",
            )
        )
    ],
)
def publish_ticket(
    ticket: Annotated[Ticket, Depends(get_ticket_or_404)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> PublishTicketResponse:
    # 質問者は非公開->公開に変更できない(unpublish側のみ許可)
    # --- 状態チェック: すでに公開の場合は無意味な操作として422(BusinessException)を返す ---
    if ticket.visibility == TicketVisibilityType.PUBLIC:
        raise BusinessException("既に公開設定です")

    # --- 更新処理: 公開設定を更新し、対応履歴にシステム履歴を追加する
    #     (Ticketの更新とTicketCommentの追加を同一トランザクションでコミットする)
    #     対象visibilityはPUBLIC固定のため、表示名はクライアント入力を経由せずベタ書きする ---
    ticket.visibility = TicketVisibilityType.PUBLIC

    new_comment = TicketComment(
        ticket_id=ticket.id,
        content="公開設定を「公開」に変更しました",
        created_by_user_id=user.id,
    )
    session.add(new_comment)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"failed to publish ticket {e}")
        raise e

    return PublishTicketResponse(
        id=ticket.id, visibility=ticket.visibility, updated_at=ticket.updated_at
    )


# ------------------------


# 公開 → 非公開
@router.put("/{ticket_id}/unpublish", response_model=UnpublishTicketResponse)
def unpublish_ticket(
    ticket: Annotated[Ticket, Depends(get_ticket_or_404)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> UnpublishTicketResponse:
    # --- 状態チェック: すでに非公開の場合は無意味な操作として422(BusinessException)を返す ---
    if ticket.visibility == TicketVisibilityType.PRIVATE:
        raise BusinessException("既に非公開設定です")

    # --- 権限チェック: ADMIN/SUPPORT(担当の有無を問わず全チケット対象)、または質問者本人のみ変更可能 ---
    is_admin_or_support = user.role in (UserRoleType.ADMIN, UserRoleType.SUPPORT)
    is_questioner = ticket.created_by_user_id == user.id
    if not is_admin_or_support and not is_questioner:
        raise ForbiddenException("質問者、サポート担当、または管理者のみ公開設定を変更できます")

    # --- 更新処理: 公開設定を更新し、対応履歴にシステム履歴を追加する
    #     (Ticketの更新とTicketCommentの追加を同一トランザクションでコミットする)
    #     対象visibilityはPRIVATE固定のため、表示名はクライアント入力を経由せずベタ書きする ---
    ticket.visibility = TicketVisibilityType.PRIVATE

    new_comment = TicketComment(
        ticket_id=ticket.id,
        content="公開設定を「非公開」に変更しました",
        created_by_user_id=user.id,
    )
    session.add(new_comment)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"failed to unpublish ticket {e}")
        raise e

    return UnpublishTicketResponse(
        id=ticket.id, visibility=ticket.visibility, updated_at=ticket.updated_at
    )
