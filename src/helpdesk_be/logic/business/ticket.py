# validation_exception_handlerでも同じ文言を使うため定数化している
BLANK_MESSAGE = "空欄では登録できません"


def not_blank(v: str) -> str:
    # 前後の空白のみの入力は未入力とみなしてNG（min_lengthだけでは空白のみの文字列を弾けないため）
    if not v.strip():
        raise ValueError(BLANK_MESSAGE)
    return v
