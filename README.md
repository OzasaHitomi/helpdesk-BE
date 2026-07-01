

### 動作環境


* Node.js 26.4.0 (2026-06-30現在最新バージョン)
* Python 3.14 (2026-06-30現在最新バージョン)
* Poetry 2.3.3
* Docker Desktop.

---
&nbsp;  
### 2.1 リポジトリをクローン

```bash
git clone git@github.com:OzasaHitomi/helpdesk-BE.git
```
&nbsp;  
---
&nbsp;  
### 2.2 poetry設定

```bash
# Poetryインストール（入っていない場合）
# homebrewからinstallする場合の例
brew install poetry

# 依存ライブラリ
poetry install
```
&nbsp;  
---
&nbsp;  
### 2.3 環境変数

`.env.example` を参考に、.envファイルをルートディレクトリに作成し必要な値を設定する。

&nbsp;  

---
&nbsp;  
### ２.4 Docker起動(バックエンド起動)
* 開発環境のDocker起動
```bash
docker compose up -d
```
* testのDocker起動
```bash
docker compose -f docker-compose.test.yml up -d
```
&nbsp;  
---
&nbsp;  
### 2.5 動作確認URL

* 開発環境
```
http://localhost:8000
```

* 開発環境のSwagger
```
http://localhost:8000/docs
```
* テスト環境
```
http://localhost:8001
```

* テスト環境のSwagger
```
http://localhost:8001/docs
```

