# Lintチェックを実行（コードの問題点を検出）
.PHONY: lint
lint:
	poetry run ruff check .


# 自動修正可能なLintエラーを修正
.PHONY: lint-fix
lint-fix:
	poetry run ruff check . --fix

# フォーマット違反を検出（修正はしない）
.PHONY: format-check
format-check:
	poetry run ruff format . --check

# コードをフォーマット
.PHONY: format
format:
	poetry run ruff format .

# Lintチェックとフォーマットをまとめて実行
.PHONY: check
check: lint format-check
