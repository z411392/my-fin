import os
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def stub_external_deps_if_ci():
    """在 CI 或測試環境下自動 Stub 外部依賴 (yfinance, Shioaji, LLM 等)"""
    # 總是啟用 stub 以加速測試 (yfinance API 會很慢)
    should_stub = (
        os.environ.get("GITHUB_ACTIONS") == "true"
        or os.environ.get("MOCK_TESTS", "1") == "1"
    )

    if should_stub:
        # 1. External Adapters (Shared)
        # Yahoo Finance
        p1 = patch(
            "libs.monitoring.src.adapters.driven.yahoo.market_data_adapter.YahooMarketDataAdapter"
        )
        stub_yahoo = p1.start()
        stub_yahoo.return_value.get_vix.return_value = 14.5

        # StatementDog
        p2 = patch(
            "libs.shared.src.clients.statementdog.statement_dog_client.StatementDogClient"
        )
        stub_sd = p2.start()
        stub_sd_instance = stub_sd.return_value
        stub_sd_instance.get_fundamental_summary.return_value = {
            "is_valid": True,
            "revenue_momentum": {
                "is_accelerating": True,
                "short_term_yoy": 15.0,
                "long_term_yoy": 12.0,
                "current_yoy": 18.0,
            },
            "earnings_quality": {"is_quality": True},
            "valuation_metrics": {"is_safe": True, "current_pe": 12.0},
        }

        # Stub ScanPairsQuery (Shared)
        p_pairs = patch(
            "libs.hunting.src.application.queries.scan_pairs.ScanPairsQuery"
        )
        stub_pairs = p_pairs.start()
        stub_pairs.return_value.execute.return_value = {"pairs": []}

        # Stub ScanResidualMomentumQuery (Shared)
        p_momentum = patch(
            "libs.hunting.src.application.queries.scan_residual_momentum.ScanResidualMomentumQuery"
        )
        stub_momentum = p_momentum.start()
        stub_momentum.return_value.execute.return_value = {
            "top_targets": [
                {
                    "symbol": "2330",
                    "name": "台積電",
                    "closing_price": 580.0,
                    "momentum": 2.5,  # Changed from residual_momentum to match new report key
                    "residual_momentum": 2.5,
                    "r_squared": 0.85,
                    "industry": "半導體",
                    "max_ret": 0.05,
                }
            ],
            "bottom_targets": [],
        }

        # LLM - 跳過 patch 避免 langchain import segfault
        # 測試時 LLM 會透過環境變數落入 fake adapter
        # (不 patch gemini_llm_adapter，改用 LlmFakeAdapter 自動替代)

        # 2. Daily Report Helpers (包含從週報合併的功能)
        daily_cls = "libs.reporting.src.application.commands.generate_daily_report.GenerateDailyReportCommand"
        patch(
            f"{daily_cls}._calculate_hmm_state_and_prob", return_value=(1, 0.85)
        ).start()
        patch(f"{daily_cls}._calculate_hurst", return_value=0.65).start()
        patch(f"{daily_cls}._calculate_pca_stability", return_value=0.95).start()
        patch(f"{daily_cls}._calculate_gli_z", return_value=1.2).start()
        patch(
            f"{daily_cls}._get_liquidity_quadrant",
            return_value={
                "name": "EXPANSION",
                "emoji": "🟢",
                "m2_yoy": 5.2,
                "fed_trend": "expanding",
            },
        ).start()
        patch(
            f"{daily_cls}._get_stock_pairs",
            return_value={
                "pair_with": "FakeStock",
                "correlation": 0.85,
                "z_score": 1.2,
            },
        ).start()
        # CVaR 計算 Stub
        patch(
            f"{daily_cls}._calculate_portfolio_cvar",
            return_value={"cvar_95": -1.8, "var_95": -1.2, "tail_risk": "🟢 正常"},
        ).start()
        # Stub 從週報遷移的功能
        patch(
            f"{daily_cls}._get_pairs_opportunities",
            return_value=[
                {
                    "pair": "2330/2303",
                    "correlation": 0.95,
                    "z_score": 2.1,
                    "half_life": 10,
                    "signal": "做空價差",
                }
            ],
        ).start()
        patch(
            f"{daily_cls}._get_supply_chain_opportunities",
            return_value=[],
        ).start()

        # 3. Weekly Report Helpers
        weekly_cls = "libs.reporting.src.application.commands.generate_weekly_report.GenerateWeeklyReportCommand"
        # Stub performance data to avoid Shioaji/Yahoo
        patch(
            f"{weekly_cls}._get_performance",
            return_value={
                "mtd_return": 0.035,
                "ytd_return": 0.128,
                "sharpe_ratio": 1.8,
                "win_rate": 0.55,
                "max_drawdown": -0.05,
                "profit_factor": 1.5,
                "avg_win": 0.04,
                "avg_loss": -0.02,
            },
        ).start()

        # 4. CRITICAL: Stub _send_email to prevent real emails during tests
        patch(f"{daily_cls}._send_email", return_value=True).start()
        patch(f"{weekly_cls}._send_email", return_value=True).start()

        yield

        patch.stopall()
    else:
        yield
