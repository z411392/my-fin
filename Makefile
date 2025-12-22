-include .env
export

.PHONY: scan daily weekly sync-data monitor retain summary stock format lint test

RUN = PYTHONPATH=. uv run python

# ============================================
# 主要指令 (4 個)
# ============================================

scan:
ifdef SYMBOL
	@$(RUN) apps/scanning/src/main.py scan --start_from=$(SYMBOL)
else
	@$(RUN) apps/scanning/src/main.py scan
endif

daily:
	@$(RUN) apps/reporting/src/main.py daily

weekly:
	@$(RUN) apps/reporting/src/main.py weekly

sync-data:
	@$(RUN) apps/maintaining/src/main.py sync

monitor:
	@$(RUN) apps/scanning/src/main.py monitor

retain:
	@$(RUN) apps/scanning/src/main.py retain $(SYMBOL)

summary:
	@$(RUN) apps/reporting/src/main.py summary $(DATE)

stock:
	@$(RUN) apps/reporting/src/main.py stock $(DATE) $(SYMBOL)

# ============================================
# 分離式掃描指令 (動能評估 / 財報狗分開執行)
# ============================================

scan-momentum:
ifdef START_FROM
	@$(RUN) apps/scanning/src/main.py scan_momentum --start_from=$(START_FROM)
else
	@$(RUN) apps/scanning/src/main.py scan_momentum
endif

scan-fundamental:
ifdef START_FROM
	@$(RUN) apps/scanning/src/main.py scan_fundamental --start_from=$(START_FROM)
else
	@$(RUN) apps/scanning/src/main.py scan_fundamental
endif

retain-momentum:
	@$(RUN) apps/scanning/src/main.py retain_momentum $(SYMBOL)

retain-fundamental:
	@$(RUN) apps/scanning/src/main.py retain_fundamental $(SYMBOL)

# ============================================
# 開發工具 (Code Quality)
# ============================================

# Ruff: 程式碼風格檢查 (linting)
lint:
	@echo "🔍 Ruff lint..."
	@uvx ruff check apps/ libs/

# Ruff: 程式碼格式化
format:
	@echo "✨ Ruff format..."
	@uvx ruff format apps/ libs/

# Vulture: 找出未使用的程式碼
deadcode:
	@echo "💀 Vulture dead code..."
	@uvx vulture apps/ libs/ --min-confidence 80

# 測試
test:
	@echo "🧪 Running tests..."
	@uv run pytest libs/*/tests/unit -v --ignore=libs/calculators --ignore=libs/statementdog --ignore=libs/reviewing/tests/unit/queries/test_check_alpha_decay.py --ignore=libs/reviewing/tests/unit/queries/test_get_skill_metrics.py 2>/dev/null || uv run pytest libs/*/tests/unit -v --ignore=libs/reviewing/tests/unit/queries/test_check_alpha_decay.py --ignore=libs/reviewing/tests/unit/queries/test_get_skill_metrics.py