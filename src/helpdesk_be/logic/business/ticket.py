def not_blank(v: str) -> str:
    # 前後の空白のみの入力は未入力とみなしてNG（min_lengthだけでは空白のみの文字列を弾けないため）
    if not v.strip():
        raise ValueError("空欄では登録できません")
    return v
