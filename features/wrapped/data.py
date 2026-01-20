#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""osu! 2025 Wrapped データ取得・処理モジュール"""

from datetime import datetime
from typing import Optional, Dict, List
from core.osu_api import OsuAPIClient
from core.utils import get_modded_star_rating_from_api
from core.logger import get_logger

logger = get_logger("wrapped")


def filter_2025_scores(scores: List[Dict], year: int = 2025) -> List[Dict]:
    """指定された年のスコアをフィルタリング"""
    filtered_scores = []
    
    for score in scores:
        # created_at のフォーマット例: "2025-01-15T12:30:45Z"
        created_at = score.get('created_at', '')
        if created_at:
            try:
                score_date = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ')
                if score_date.year == year:
                    filtered_scores.append(score)
            except ValueError:
                continue
    
    return filtered_scores


def calculate_2025_playcount(user_data: Dict, year: int = 2025) -> int:
    """月ごとのプレイカウントデータから2025年のトータルプレイカウントを計算"""
    monthly_playcounts = user_data.get('monthly_playcounts', [])
    
    if not monthly_playcounts:
        return 0
    
    total_2025_plays = 0
    
    for month_data in monthly_playcounts:
        # start_date のフォーマット例: "2025-01-01"
        start_date = month_data.get('start_date', '')
        count = month_data.get('count', 0)
        
        if start_date:
            try:
                date = datetime.strptime(start_date, '%Y-%m-%d')
                if date.year == year:
                    total_2025_plays += count
            except ValueError:
                continue
    
    return total_2025_plays


def get_monthly_2025_data(user_data: Dict, year: int = 2025) -> List[Dict]:
    """2025年の月別プレイカウントデータを取得"""
    monthly_playcounts = user_data.get('monthly_playcounts', [])
    monthly_2025_data = []
    
    for month_data in monthly_playcounts:
        start_date = month_data.get('start_date', '')
        count = month_data.get('count', 0)
        
        if start_date:
            try:
                date = datetime.strptime(start_date, '%Y-%m-%d')
                if date.year == year:
                    monthly_2025_data.append({
                        'month': date.strftime('%Y-%m'),
                        'count': count
                    })
            except ValueError:
                continue
    
    monthly_2025_data.sort(key=lambda x: x['month'])
    return monthly_2025_data


def get_2025_stats_data(username: str, client_id: str, client_secret: str) -> Optional[Dict]:
    """2025年の統計情報を取得して辞書形式で返す（Discord Bot用）"""
    try:
        # APIクライアントの初期化
        logger.debug(f"OsuAPIClient初期化: username={username}")
        client = OsuAPIClient(client_id, client_secret)
        
        # ユーザー情報の取得
        logger.debug(f"ユーザー情報取得API呼び出し: username={username}")
        user = client.get_user(username)
        
        if not user:
            logger.warning(f"ユーザー情報の取得に失敗（ユーザーが見つかりません）: username={username}")
            return None
        
        user_id = user['id']
        logger.debug(f"ユーザー情報取得成功: username={username}, user_id={user_id}")
        
        # ベストスコアの取得
        logger.debug(f"ベストスコア取得API呼び出し: user_id={user_id}")
        best_scores = client.get_user_best_scores(user_id, limit=100)
        logger.debug(f"ベストスコア取得完了: user_id={user_id}, count={len(best_scores)}")
        
        # 2025年のスコアをフィルタリング
        scores_2025 = filter_2025_scores(best_scores, year=2025)
        logger.debug(f"2025年スコアフィルタリング完了: username={username}, scores_2025_count={len(scores_2025)}")
        
        # PPでソート（降順）
        if scores_2025:
            scores_2025.sort(key=lambda x: x.get('pp', 0), reverse=True)
            top_10_scores = scores_2025[:10]
            
            # 各スコアにMOD適用後のStar Ratingを追加（APIから取得）
            logger.debug(f"MOD適用後Star Rating取得開始: username={username}, top_10_count={len(top_10_scores)}")
            for idx, score in enumerate(top_10_scores, 1):
                try:
                    modded_sr = get_modded_star_rating_from_api(score, client)
                    score['_modded_star_rating'] = modded_sr
                except Exception as sr_error:
                    logger.warning(f"Star Rating取得エラー (score #{idx}): username={username}, error={sr_error}")
            logger.debug(f"MOD適用後Star Rating取得完了: username={username}")
        else:
            top_10_scores = []
        
        # プレイカウントの計算
        plays_2025 = calculate_2025_playcount(user, year=2025)
        monthly_2025_data = get_monthly_2025_data(user, year=2025)
        total_playcount = user.get('statistics', {}).get('play_count', 0)
        logger.debug(f"プレイカウント計算完了: username={username}, total={total_playcount}, 2025={plays_2025}, monthly_count={len(monthly_2025_data)}")
        
        return {
            'user': user,
            'scores_2025': scores_2025,
            'top_10_scores': top_10_scores,
            'plays_2025': plays_2025,
            'monthly_2025_data': monthly_2025_data,
            'total_playcount': total_playcount
        }
    except Exception as e:
        logger.error(f"get_2025_stats_data error: username={username}, error={str(e)}", exc_info=True)
        return None

