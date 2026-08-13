from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.auth import get_current_user
from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.exceptions.business_exception import BusinessException
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.exceptions.not_found_exception import NotFoundException
from helpdesk_be.loggers.custom_logger import logger
from helpdesk_be.logic.business.ticket_permission import can_view_ticket
from helpdesk_be.models.ticket import Ticket
from helpdesk_be.models.ticket_comment import TicketComment
from helpdesk_be.models.user import User
from helpdesk_be.repositories.ticket import get_ticket_by_id, get_tickets_with_users
from helpdesk_be.repositories.ticket_comment import get_comments_with_users_by_ticket_id
from helpdesk_be.schemas.request.v1.ticket import CreateTicketRequest
from helpdesk_be.schemas.request.v1.ticket_comment import CreateTicketCommentRequest
from helpdesk_be.schemas.response.v1.ticket import (
    AssignTicketResponse,
    CreateTicketResponse,
    GetTicketResponse,
    GetTicketsResponseItem,
    UnassignTicketResponse,
)
from helpdesk_be.schemas.response.v1.ticket_comment import (
    CreateTicketCommentResponse,
    GetTicketCommentsResponseItem,
)
from helpdesk_be.store.enum.ticket_status_type import TicketStatusType
from helpdesk_be.store.enum.user_role_type import UserRoleType

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreateTicketResponse)
def create_ticket(
    body: CreateTicketRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> CreateTicketResponse:
    # チケットの新規作成は社員アカウントのみ許可する
    if user.role != UserRoleType.EMPLOYEE:
        raise ForbiddenException("社員アカウントのみチケットを作成できます")

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
    ticket_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> GetTicketResponse:
    ticket = get_ticket_by_id(session, ticket_id)

    # 存在しない場合、および非公開チケットをSUPPORT/ADMIN以外かつ本人(質問者)以外が閲覧しようとした場合は
    # チケットの存在有無を推測させないよう404で統一する(fail-closed)
    if ticket is None:
        raise NotFoundException("チケットが見つかりません")

    if not can_view_ticket(user, ticket):
        raise NotFoundException("チケットが見つかりません")

    return GetTicketResponse(
        id=ticket.id,
        title=ticket.title,
        detail=ticket.detail,
        visibility=ticket.visibility,
        status=ticket.status,
        support_user_id=ticket.support_user_id,
        support_user_name=ticket.support_user.name if ticket.support_user else None,
        created_at=ticket.created_at,
    )


# ------------------------


@router.get("/{ticket_id}/comments", response_model=list[GetTicketCommentsResponseItem])
def list_ticket_comments(
    ticket_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[GetTicketCommentsResponseItem]:
    ticket = get_ticket_by_id(session, ticket_id)

    # 対応履歴の閲覧可否はチケット詳細の閲覧可否と同一ルールのためcan_view_ticketを再利用する。
    # 存在しない場合、および閲覧不可の場合はチケットの存在有無を推測させないよう404で統一する(fail-closed)
    if ticket is None or not can_view_ticket(user, ticket):
        raise NotFoundException("チケットが見つかりません")

    comments = get_comments_with_users_by_ticket_id(session, ticket.id)

    # TicketCommentモデルのリストをレスポンススキーマへ変換する。
    # commenterはコメントの投稿者(User)とのリレーションで、その名前をcommenter_nameとして詰め替えている。
    # 投稿者がいない行(created_by_user_id=NULL)は担当者割り当て等でシステムが自動登録した履歴のため、
    # 対応者は"system"と表示する
    return [
        GetTicketCommentsResponseItem(
            id=comment.id,
            content=comment.content,
            commenter_name=(comment.commenter.name if comment.commenter is not None else "system"),
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
    ticket_id: int,
    body: CreateTicketCommentRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> CreateTicketCommentResponse:
    ticket = get_ticket_by_id(session, ticket_id)

    # 投稿権限は閲覧権限と同一(閲覧できるチケットには誰でも投稿できる仕様)のためcan_view_ticketを再利用する。
    # 存在しない場合、および閲覧不可の場合はチケットの存在有無を推測させないよう404で統一する(fail-closed)
    if ticket is None or not can_view_ticket(user, ticket):
        raise NotFoundException("チケットが見つかりません")

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


@router.put("/{ticket_id}/assign", response_model=AssignTicketResponse)
def assign_ticket_to_self(
    ticket_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> AssignTicketResponse:
    # --- 権限チェック: 担当者の自己アサインはサポート担当のみ許可する ---
    if user.role != UserRoleType.SUPPORT:
        raise ForbiddenException("サポート担当のみこの操作を実行できます")

    # --- 存在チェック: 指定したチケットが存在しない場合は404 ---
    ticket = get_ticket_by_id(session, ticket_id)
    if ticket is None:
        raise NotFoundException("チケットが見つかりません")

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
    ticket_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> UnassignTicketResponse:
    # --- 存在チェック: 指定したチケットが存在しない場合は404 ---
    ticket = get_ticket_by_id(session, ticket_id)
    if ticket is None:
        raise NotFoundException("チケットが見つかりません")

    # --- 本人チェック: 自分が担当しているチケットのみ解除できる。
    #     support_user_idはSUPPORTロールのユーザーしかセットされない(assign_ticket_to_self参照)ため、
    #     このチェック1つでロール違い・未担当・別担当者のケースを全てカバーできる ---
    if ticket.support_user_id != user.id:
        raise ForbiddenException("自分が担当しているチケットのみ担当解除できます")

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
