#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Twitch API v2 クライアントモジュール"""

import requests
from typing import Optional, Dict, List


class TwitchAPIClient:
    """Twitch API v2 クライアント"""
    
    TOKEN_URL = "https://id.twitch.tv/oauth2/token"
    BASE_URL = "https://api.twitch.tv/helix"
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self._authenticate()
    
    def _authenticate(self):
        """APIアクセストークンの取得"""
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        
        response = requests.post(self.TOKEN_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
    
    def _get_headers(self) -> Dict[str, str]:
        """認証ヘッダーの取得"""
        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}"
        }
    
    def get_user_ids(self, usernames: List[str]) -> Dict[str, str]:
        """ユーザー名からユーザーIDを取得"""
        url = f"{self.BASE_URL}/users"
        headers = self._get_headers()
        params = {"login": usernames}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        user_ids = {}
        for user in data.get("data", []):
            user_ids[user["login"]] = user["id"]
        
        return user_ids
    
    def get_streams(self, user_ids: List[str]) -> List[Dict]:
        """配信状況を取得"""
        if not user_ids:
            return []
        
        url = f"{self.BASE_URL}/streams"
        headers = self._get_headers()
        
        # Twitch APIは最大100ユーザーIDまで一度に取得可能
        # 100を超える場合は分割してリクエスト
        all_streams = []
        for i in range(0, len(user_ids), 100):
            batch = user_ids[i:i+100]
            params = {"user_id": batch}
            
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                all_streams.extend(data.get("data", []))
            except Exception as e:
                # エラー時は次のバッチに進む
                print(f"[ERROR] Twitch配信取得エラー (batch {i//100 + 1}): {e}")
                continue
        
        return all_streams

