def user_password(v: str) -> str:
    # 8文字未満はNG
    if len(v) < 8:
        raise ValueError("パスワードは8文字以上で入力してください")
    # 数字を1文字も含まない場合はNG
    if not any(c.isdigit() for c in v):
        raise ValueError("パスワードには数字を1文字以上含めてください")
    # 大文字を1文字も含まない場合はNG
    if not any(c.isupper() for c in v):
        raise ValueError("パスワードには大文字を1文字以上含めてください")
    return v
