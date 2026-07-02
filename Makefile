# Lintチェックを実行（コードの問題点を検出）
.PHONY: lint
lint:
	ruff check .

# 自動修正可能なLintエラーを修正
.PHONY: lint-fix
lint-fix:
	ruff check . --fix

# コードをフォーマット
.PHONY: format
format:
	ruff format .

# Lintチェックとフォーマットをまとめて実行
.PHONY: check
check: lint format
