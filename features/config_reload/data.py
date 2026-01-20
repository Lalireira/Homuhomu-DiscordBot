#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""設定リロード データ処理ロジック"""

from typing import Dict, Any
from dotenv import load_dotenv
from core.logger import get_logger
from core.config import (
    get_osu_credentials,
    get_twitch_credentials,
    get_twitch_config,
    get_notification_role_id,
    get_broadcast_allowed_users
)

logger = get_logger("config_reload")


def reload_environment_config() -> Dict[str, Any]:
    """
    環境変数を再読み込みする（Bot Token以外のすべての設定項目）
    
    Returns:
        リロード結果（成功/失敗、再読み込みされた設定情報）
    """
    try:
        # 環境変数を再読み込み（override=Trueで既存の環境変数を上書き）
        load_dotenv(override=True)
        logger.info("環境変数を再読み込みしました")
        
        # 再読み込み後にすべての設定を取得（Bot Tokenは除外）
        config = {}
        
        # osu! API認証情報
        osu_client_id, osu_client_secret = get_osu_credentials()
        config["osu_api"] = {
            "client_id": "設定済み" if osu_client_id else "未設定",
            "client_secret": "設定済み" if osu_client_secret else "未設定"
        }
        
        # Twitch API認証情報
        twitch_client_id, twitch_client_secret = get_twitch_credentials()
        config["twitch_api"] = {
            "client_id": "設定済み" if twitch_client_id else "未設定",
            "client_secret": "設定済み" if twitch_client_secret else "未設定"
        }
        
        # Twitch通知設定
        twitch_config = get_twitch_config()
        config["twitch_notification"] = {
            "channel_id": twitch_config.get("channel_id"),
            "usernames": twitch_config.get("usernames", []),
            "check_interval": twitch_config.get("check_interval")
        }
        
        # 通知ロール設定
        notification_role_id = get_notification_role_id()
        config["notification_role"] = {
            "role_id": notification_role_id
        }
        
        # 通知チャンネル設定（未使用だが設定可能な場合のみ表示）
        # notification_channel_id = get_notification_channel_id()
        # config["notification_channel"] = {
        #     "channel_id": notification_channel_id
        # }
        
        # Broadcast許可ユーザー設定
        broadcast_allowed_users = get_broadcast_allowed_users()
        config["broadcast"] = {
            "allowed_users": broadcast_allowed_users
        }
        
        result = {
            "success": True,
            "config": config
        }
        
        return result
        
    except Exception as e:
        logger.error(f"環境変数再読み込みエラー: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
