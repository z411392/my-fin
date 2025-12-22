"""Shioaji Client Wrapper

提供連線管理功能，供各 BC 的 Adapters 引用。
"""

import os
import sys
import io
import warnings
import logging
import base64
import uuid
import tempfile
import pathlib
from typing import Any

import shioaji as sj


class ShioajiClient:
    """Shioaji 連線管理器

    Usage:
        client = ShioajiClient(simulation=True)
        if client.connect():
            api = client.api
            # 使用 api 進行操作
            client.disconnect()
    """

    def __init__(self, simulation: bool = True) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._api: Any = None
        self._connected = False
        self._simulation = simulation

    @property
    def api(self) -> Any:
        """取得 Shioaji API 實例"""
        return self._api

    @property
    def connected(self) -> bool:
        """是否已連線"""
        return self._connected

    def connect(self) -> None:
        """連線到 Shioaji API (抑制冗餘訊息)"""

        api_key = os.environ.get("SHIOAJI_API_KEY")
        secret = os.environ.get("SHIOAJI_SECRET")

        if not all([api_key, secret]):
            self._logger.warning("缺少 SHIOAJI_API_KEY 或 SHIOAJI_SECRET")
            return False

        # 抑制 Shioaji 相關的 log 和 warnings
        logging.getLogger("shioaji").setLevel(logging.CRITICAL)
        logging.getLogger("pysolace").setLevel(logging.CRITICAL)
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        try:
            # 抑制初始化時的 stderr 輸出
            stderr_backup = sys.stderr
            sys.stderr = io.StringIO()
            try:
                self._api = sj.Shioaji(simulation=self._simulation)
                self._api.login(api_key=api_key, secret_key=secret)
            finally:
                sys.stderr = stderr_backup
            self._connected = True
            return True
        except Exception as e:
            self._logger.warning(f"Shioaji 連線失敗: {e}")
            return False

    def disconnect(self) -> None:
        """斷開連線 (抑制 logout timeout 訊息)"""
        if self._api and self._connected:
            # 抑制 Shioaji logout 時的 stderr 輸出
            stderr_backup = sys.stderr
            sys.stderr = io.StringIO()
            try:
                self._api.logout()
            except Exception:
                pass
            finally:
                sys.stderr = stderr_backup
            self._connected = False

    def _get_ca_path_from_base64(self) -> str | None:
        """從 SINOPAC_PFX_BASE64 環境變數解碼憑證到臨時檔案"""

        pfx_base64 = os.environ.get("SINOPAC_PFX_BASE64")
        if not pfx_base64:
            return None

        try:
            pfx_bytes = base64.b64decode(pfx_base64)
            random_name = f"sinopac_{uuid.uuid4().hex}.pfx"
            tmp_path = pathlib.Path(tempfile.gettempdir()) / random_name
            tmp_path.write_bytes(pfx_bytes)
            return str(tmp_path)
        except Exception:
            return None

    def activate_ca(
        self,
        ca_path: str | None = None,
        ca_password: str | None = None,
        person_id: str | None = None,
    ) -> bool:
        """啟用憑證 (正式交易環境需要)

        優先順序：
        1. 傳入參數 ca_path
        2. 環境變數 SHIOAJI_CA_PATH (檔案路徑)
        3. 環境變數 SINOPAC_PFX_BASE64 (Base64 編碼，自動解碼到 /tmp)
        """
        if not self._connected:
            return False

        ca_path = ca_path or os.environ.get("SHIOAJI_CA_PATH")
        ca_password = ca_password or os.environ.get("SHIOAJI_CA_PASSWORD")
        person_id = person_id or os.environ.get("SHIOAJI_PERSON_ID")

        # 如果沒有 ca_path，嘗試從 Base64 環境變數解碼
        if not ca_path:
            ca_path = self._get_ca_path_from_base64()

        if not all([ca_path, ca_password, person_id]):
            return False

        try:
            self._api.activate_ca(
                ca_path=ca_path,
                ca_passwd=ca_password,
                person_id=person_id,
            )
            return True
        except Exception:
            return False

    def __enter__(self) -> "ShioajiClient":
        self.connect()
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        self.disconnect()
