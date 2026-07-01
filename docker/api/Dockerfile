#イメージを引っ張ってきている。最新版のバージョン指定
FROM python:3.14

#指定した名前のディレクトリ内で作業するという宣言。
WORKDIR /helpdesk_be

#tzdata：タイムゾーンの概念のインストール
#apt-get:Macなどの根本で動いているところのLinuxのコマンド
RUN apt-get update && \
  apt-get install -y --no-install-recommends tzdata && \
  rm -rf /var/lib/apt/lists/*

# Poetryのインストール
# homebrewをわざわざ入れる必要がないのでpipを使用
RUN pip install poetry

# Poetryの仮想環境は使わずグローバルに（Docker内ではこれがシンプル）
RUN poetry config virtualenvs.create false

#dockerコンテナ内に設計書のコピーをdocker内にも作る
COPY pyproject.toml poetry.lock ./
#poetry install:環境作成
#--no-root --only main:本番環境だけで動かすものだけをコンテナ内に入れる
RUN poetry install --no-root --only main

# アプリケーションのソースコードをコピー
COPY . .

#CMD:commandの略
#uvicorn：fastapiの立ち上げに使う
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
