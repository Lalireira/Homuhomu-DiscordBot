#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""osu! API v2 クライアントモジュール"""

import requests
from typing import Optional, Dict, List


class OsuAPIClient:
    """osu! API v2 クライアント"""
    
    BASE_URL = "https://osu.ppy.sh/api/v2"
    TOKEN_URL = "https://osu.ppy.sh/oauth/token"
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self._authenticate()
    
    def _authenticate(self):
        """APIアクセストークンの取得"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'scope': 'public'
        }
        
        response = requests.post(self.TOKEN_URL, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data['access_token']
    
    def _get_headers(self) -> Dict[str, str]:
        """認証ヘッダーの取得"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_user(self, username: str, mode: str = 'osu') -> Optional[Dict]:
        """ユーザー情報の取得"""
        url = f"{self.BASE_URL}/users/{username}/{mode}"
        
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        return response.json()
    
    def get_user_recent_activity(self, user_id: int, limit: int = 100) -> List[Dict]:
        """ユーザーの最近のアクティビティを取得"""
        url = f"{self.BASE_URL}/users/{user_id}/recent_activity"
        params = {'limit': limit}
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_user_best_scores(self, user_id: int, mode: str = 'osu', limit: int = 100) -> List[Dict]:
        """ユーザーのベストスコア（PP）を取得"""
        url = f"{self.BASE_URL}/users/{user_id}/scores/best"
        params = {'mode': mode, 'limit': limit}
        
        response = requests.get(url, headers=self._get_headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_beatmap(self, beatmap_id: int) -> Optional[Dict]:
        """譜面情報の取得"""
        url = f"{self.BASE_URL}/beatmaps/{beatmap_id}"
        
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        return response.json()
    
    def get_beatmap_attributes(self, beatmap_id: int, mods: List[str] = None) -> Optional[Dict]:
        """MOD適用後の譜面属性を取得（難易度情報を含む）"""
        url = f"{self.BASE_URL}/beatmaps/{beatmap_id}/attributes"
        
        # MODのビットマスクを計算
        mod_bitmask = 0
        if mods:
            mod_to_bit = {
                'NF': 1, 'EZ': 2, 'TD': 4, 'HD': 8, 'HR': 16, 'SD': 32, 'DT': 64, 'RX': 128,
                'HT': 256, 'NC': 512, 'FL': 1024, 'AT': 2048, 'SO': 4096, 'AP': 8192, 'PF': 16384,
                '4K': 32768, '5K': 65536, '6K': 131072, '7K': 262144, '8K': 524288, 'FI': 1048576,
                'RD': 2097152, 'CN': 4194304, 'TP': 8388608, 'K9': 16777216, 'KC': 33554432,
                '1K': 67108864, '3K': 134217728, '2K': 268435456, 'V2': 536870912, 'MR': 1073741824
            }
            
            for mod in mods:
                if mod in mod_to_bit:
                    mod_bitmask |= mod_to_bit[mod]
                # NCはDTを含む（NCが指定されている場合はDTも含める）
                if mod == 'NC' and 'DT' not in mods:
                    mod_bitmask |= mod_to_bit['DT']
        
        # POSTリクエストでmodsパラメータを送信
        payload = {'mods': mod_bitmask} if mod_bitmask > 0 else {}
        response = requests.post(url, headers=self._get_headers(), json=payload)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        return response.json()

