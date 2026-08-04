from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.auth import get_current_user
from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.exceptions.not_found_exception import NotFoundException
from helpdesk_be.logic.business.ticket_permission import can_view_ticket
from helpdesk_be.models.user import User
from helpdesk_be.repositories.ticket import get_ticket_by_id
from helpdesk_be.repositories.ticket_comment import get_comments_with_users_by_ticket_id
from helpdesk_be.schemas.response.v1.ticket_comment import GetTicketCommentsResponseItem

router = APIRouter()


@router.get("", response_model=list[GetTicketCommentsResponseItem])
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
