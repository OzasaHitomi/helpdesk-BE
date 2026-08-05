from typing import Annotated

from pydantic import StringConstraints

from helpdesk_be.schemas.request.v1.base import BaseV1RequestSchema

# 前後の空白を除去した上でmin_lengthを判定する(空白のみの入力は未入力とみなしてNGにするため)
# schemas/request/v1/ticket.pyのNotBlankStrと同じ定義だが、コメント固有のバリデーションルールを
# base.pyに混ぜたくないためあえて重複させている
NotBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


# チケット対応履歴(質問・返信)投稿APIのリクエストボディを表すスキーマ
class CreateTicketCommentRequest(BaseV1RequestSchema):
    content: NotBlankStr
