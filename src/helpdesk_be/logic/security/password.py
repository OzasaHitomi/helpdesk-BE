import bcrypt


def hash_password(plain_password: str) -> str:
    # gensalt()でランダムなソルト（文字列）を生成し、平文PWと混ぜてハッシュ化する
    # ソルトを混ぜることで、同じPWでも毎回異なるハッシュ値になり、レインボーテーブル攻撃を防げる
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    # DB保存やAPIレスポンスで扱いやすいよう、bytes型からstr型に変換して返す
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # ハッシュ文字列内にソルト情報も含まれているため、
    # 保存済みハッシュとログイン時の平文PWを渡すだけで一致判定ができる
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
