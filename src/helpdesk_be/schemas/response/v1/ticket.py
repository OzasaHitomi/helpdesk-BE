from helpdesk_be.schemas.response.v1.base import BaseV1ResponseSchema


# チケット新規作成APIのレスポンス。FEがトースター通知（「チケット：XXXが新規登録されました」）に
# 使えるよう、登録されたチケットを特定できる項目のみを返す
# id: 現時点では未使用だが、一覧上での新規チケットのハイライトや詳細画面へのリンク等、
#     今後の実装で必要になる可能性が高いため残す
class CreateTicketResponse(BaseV1ResponseSchema):
    id: int
    title: str
