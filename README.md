## 目次
- [1. ブランチ運用ルール](#1-ブランチ運用ルール)
  - [1.1 ブランチ構成](#11-ブランチ名ブランチ構成)
  - [1.2 ブランチの切り方・マージ・被マージの流れ](#12-ブランチの切り方マージ被マージの流れ)
    - [1.2.1 ブランチの切り方](#121-ブランチの切り方)
    - [1.2.2 マージ、被マージの流れの図](#122-マージ被マージの流れの図)
    - [1.2.3 基本ルール](#123-基本ルール)
    - [1.2.4 禁止事項](#124-禁止事項)
    - [1.2.5 例外ルール](#125-例外ルール)
  - [1.3 タスクに対する使用の仕方](#13-タスクに対する使用の仕方)
    - [1.3.1 使用の仕方](#131-使用の仕方)
    - [1.3.2 コミットメッセージ Prefix](#132-コミットメッセージ-prefix)
  - [1.4 ブランチ命名規則](#14-ブランチ命名規則)
- [2. 環境構築手順](#2-環境構築手順)


## 1. ブランチ運用ルール

### 1.1 ブランチ構成

```
main
├── develop
│   ├── feature/xxx
│   ├── fix/xxx
│   └── docs/xxx
└── hotfix/xxx
```
&nbsp;  

| ブランチ名 | 役割 |
|---|---|
| `main` | 本番環境に反映される安定したコード |
| `develop` | 開発の統合ブランチ。`feature` / `fix` / `docs` の変更をまとめ、リリース時に `main` にマージする |
| `feature/xxx` | 新機能の開発。完成したら `develop` にマージ |
| `fix/xxx` | バグ修正。完成したら `develop` にマージ |
| `docs/xxx` | ドキュメントの追加・修正。完成したら `develop` にマージ |
| `hotfix/xxx` | 本番障害の緊急対応。`main` から派生し、`main` と `develop` 両方にマージ |




&nbsp; 

<fixブランチとhotfixブランチの違い>
* fixブランチ → 緊急を要さないコードの修正をする場合
* hotfixブランチ → 緊急で修正が必要な場合

&nbsp;  

### 1.2 ブランチの切り方・マージ・被マージの流れ

#### 1.2.1 ブランチの切り方

作業ブランチは以下の手順で作成する。

**① リモートの最新状態を取得する**
```bash
git fetch origin
```

**② 起点となるブランチに切り替え、最新の状態にする**

通常の開発ブランチ（feature, fix, docs）は `develop` から作成する。
```bash
git checkout develop
git pull origin develop
```

緊急修正ブランチ（hotfix）は `main` から作成する。
```bash
git checkout main
git pull origin main
```

**③ 新しいブランチを作成して切り替える**
```bash
git checkout -b feature/OIS-8-login-page
```

&nbsp;  

#### 1.2.2 マージ、被マージの流れの図
```mermaid
gitGraph
    commit id:"Initial"

    branch develop
    checkout develop
    commit id:"Develop"

    branch feature/OIS-37-login
    checkout feature/OIS-37-login
    commit id:"Login"

    checkout develop
    merge feature/OIS-37-login

    branch fix/OIS-52-login-validation
    checkout fix/OIS-52-login-validation
    commit id:"Fix Validation"

    checkout develop
    merge fix/OIS-52-login-validation

    branch docs/OIS-15-update-readme
    checkout docs/OIS-15-update-readme
    commit id:"Update README"

    checkout develop
    merge docs/OIS-15-update-readme

    checkout main
    merge develop

    branch hotfix/OIS-99-critical-bug
    checkout hotfix/OIS-99-critical-bug
    commit id:"Hotfix"

    checkout main
    merge hotfix/OIS-99-critical-bug

    checkout develop
    merge hotfix/OIS-99-critical-bug
```
&nbsp;  

#### 1.2.3 基本ルール
* `feature/*`、 `fix/*`、`docs/*` ブランチは、必ず develop ブランチから作成する。
* 機能開発・バグ修正・ドキュメント修正が完了したら、Pull Request を作成し develop ブランチへマージする。
* develop ブランチには、レビューおよび各種 CI が成功した変更のみをマージする。
* リリース時は develop ブランチを main ブランチへマージする。
* 緊急対応が必要な場合は main ブランチから hotfix/* ブランチを作成して修正を行う。
* hotfix/* ブランチは、修正完了後に main と develop の両方へマージし、修正内容の差分が発生しないようにする。
* 1つのタスクにつき 1つのブランチを作成し、複数のタスクを1つのブランチで作業しない。
* `feature/*`、`fix/*`、`docs/*` などの作業ブランチへの直接 Push は問題ないが、`main` / `develop` への直接 Push は禁止。`main` / `develop` へのマージは必ず Pull Request を経由して行う。
* 特に本番環境の重大な不具合については、通常の開発フローよりも迅速な復旧を優先し、`hotfix/*` ブランチを用いて対応する。
* 例外対応を行った場合でも、修正内容は `main` と `develop` の両方へ反映し、ブランチ間の差分が残らないようにする。

&nbsp;  

#### 1.2.4 禁止事項
* feature/ → main への直接マージは禁止
* fix/* → main への直接マージは禁止
* docs/* → main への直接マージは禁止
* feature/* 同士、fix/* 同士、docs/* 同士のマージは禁止
* develop・main への直接 Push 禁止
* レビューが完了していない Pull Request のマージ禁止
* Pull Request を作成した本人によるセルフマージ禁止

&nbsp;  

#### 1.2.5 例外ルール

基本ルールを適用できない状況が発生した場合は、独断で対応せず、チーム内で対応方針を決定する。

&nbsp;  

### 1.3 タスクに対する使用の仕方

#### 1.3.1 使用の仕方
* Jiraの1タスク = 1ブランチ
* コミットメッセージは、「prefix(type): 変更点の内容」で記述
* PRタイトルはJiraのタスク名

例

```
Jira → OIS-8 利用者はログイン画面からログインができる
branch → feature/OIS-8-user-login-from-login-screen
commit message → fix: エラーメッセージの文言修正, test: バリデーションのテスト追加
PR title → [OIS-8] 利用者はログイン画面からログインができる
```
&nbsp;  

#### 1.3.2 コミットメッセージ Prefix
Conventional Commits 規約

|type|用途|
|---|---|
|`feat`|新機能の追加|
|`fix`|バグ修正|
|`docs`|ドキュメントのみの変更|
|`style`|コードの動作に影響しない変更（フォーマット、セミコロン等）|
|`refactor`|バグ修正でも機能追加でもないコードの変更|
|`test`|テストの追加・修正|
|`chore`|ビルドプロセスや補助ツールの変更（package.jsonの更新等）|
|`perf`|パフォーマンス改善|
|`ci`|CI設定ファイルの変更|
|`revert`|以前のコミットの取り消し|

&nbsp;  

### 1.4 ブランチ命名規則

```
種別/タスク番号-内容
```
* タスク内容は、担当者が内容を適切に表現した英語で命名する。
* タスク内容には英小文字のみを使用する。
* 複数の単語で構成する場合は、単語の区切りに -（ハイフン）を使用する。

例

```
feature/OIS-8-login-page
feature/OIS-24-ticket-create
fix/OIS-17-validation-error
docs/OIS-45-readme-update
```

&nbsp;  


## 2. 環境構築手順
