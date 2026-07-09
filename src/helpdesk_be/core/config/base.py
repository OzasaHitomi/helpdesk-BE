from pydantic_settings import BaseSettings


# 初期設定。envファイルに記述がなかったらここの初期値が適用される
# envファイルの内容が優先される（）
class CoreSettings(BaseSettings):
    db_connection: str = "mysql"
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "helpdesk"
    mysql_user: str = "user"
    mysql_password: str = "pass"
    front_end_url: str = "http://localhost:5173"

    # JWTの署名・検証に使う秘密鍵。第三者に推測されないよう、.envで必ず上書きする
    # （openssl rand -hex 32 などで生成したランダムな文字列を使う）
    jwt_secret_key: str = "changeme"
    # 署名アルゴリズム。HS256（共通鍵方式）
    jwt_algorithm: str = "HS256"
    # アクセストークンの有効期限（分）
    jwt_expire_minutes: int = 60

    @property
    def database_url(self) -> str:
        return (
            f"{self.db_connection}://"
            f"{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    # ここで参照するenvファイルを指定する
    # "extra": "ignore"＝envファイルに変数を定義していても、上の変数定義（初期値の設定）にないもの（envファイルに作成した変数）は無視される。
    # allow, forbidなどもある
    model_config = {"env_file": ".env", "extra": "ignore"}


core_settings = CoreSettings()
