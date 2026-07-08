from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseV1RequestSchema(BaseModel):
    model_config = ConfigDict(
        # キャメルケースを許可＆
        # BEのスネークケースのものとキャメルケースを比較・紐付け
        alias_generator=to_camel,
        populate_by_name=True,
    )
