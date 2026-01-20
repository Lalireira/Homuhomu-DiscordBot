#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""コマンドライン版 osu! 2025 Wrapped（後方互換性のため残存）"""

import sys
import argparse
import io
from datetime import datetime
import requests
from core.config import get_osu_credentials
from core.osu_api import OsuAPIClient
from core.utils import format_mods, calculate_modded_star_rating
from features.wrapped.data import (
    get_2025_stats_data,
    filter_2025_scores,
    calculate_2025_playcount,
    get_monthly_2025_data
)

# Windows環境での文字化け対策
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def get_2025_stats(username: str, client_id: str, client_secret: str):
    """2025年の統計情報を取得（コマンドライン版）"""
    
    print(f"\nosu! 2025 Wrapped - {username}\n")
    print("=" * 80)
    
    # APIクライアントの初期化
    client = OsuAPIClient(client_id, client_secret)
    
    # ユーザー情報の取得
    print(f"\n[*] ユーザー情報を取得中...")
    user = client.get_user(username)
    
    if not user:
        print(f"[!] ユーザー '{username}' が見つかりませんでした。")
        return
    
    user_id = user['id']
    avatar_url = user['avatar_url']
    
    print(f"[OK] ユーザー: {user['username']} (ID: {user_id})")
    print(f"     アイコン: {avatar_url}")
    
    # ベストスコアの取得
    print(f"\n[*] ベストスコアを取得中...")
    best_scores = client.get_user_best_scores(user_id, limit=100)
    
    # 2025年のスコアをフィルタリング
    scores_2025 = filter_2025_scores(best_scores, year=2025)
    
    if not scores_2025:
        print(f"\n[!] 2025年のスコアが見つかりませんでした。")
        print(f"    総ベストスコア数: {len(best_scores)}")
        if best_scores:
            first_score_date = datetime.strptime(best_scores[0]['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            print(f"    最新のベストスコア: {first_score_date.strftime('%Y-%m-%d')}")
    else:
        # PPでソート（降順）
        scores_2025.sort(key=lambda x: x.get('pp', 0), reverse=True)
        
        # 上位10件を表示
        top_10_scores = scores_2025[:10]
        
        print(f"\n[TOP 10] 2025年に取得したPP")
        print("=" * 80)
        
        for i, score in enumerate(top_10_scores, 1):
            pp = score.get('pp', 0)
            beatmap = score.get('beatmap', {})
            beatmapset = score.get('beatmapset', {})
            mods = format_mods(score.get('mods', []))
            
            # 譜面情報
            artist = beatmapset.get('artist', 'Unknown')
            title = beatmapset.get('title', 'Unknown')
            difficulty = beatmap.get('version', 'Unknown')
            base_star_rating = beatmap.get('difficulty_rating', 0)
            mods_list = score.get('mods', [])
            
            # MOD適用後のStar Ratingを計算
            modded_star_rating = calculate_modded_star_rating(base_star_rating, mods_list)
            
            # カバー画像URL
            cover_url = beatmapset.get('covers', {}).get('card', '')
            
            print(f"\n{i}. {pp:.2f}pp")
            print(f"   Song: {artist} - {title}")
            print(f"   Diff: [{difficulty}] - {modded_star_rating:.2f}* {mods}")
            print(f"   Cover: {cover_url}")
            print(f"   Date: {score['created_at'][:10]}")
    
    # プレイカウントの計算
    print(f"\n[*] 2025年のプレイカウントを計算中...")
    
    # 月ごとのプレイカウントデータから2025年のトータルを計算
    plays_2025 = calculate_2025_playcount(user, year=2025)
    total_playcount = user.get('statistics', {}).get('play_count', 0)
    monthly_2025_data = get_monthly_2025_data(user, year=2025)
    
    print(f"\n[STATS] 統計情報")
    print("=" * 80)
    print(f"PLAYCOUNT (TOTAL): {total_playcount:,}")
    print(f"PLAYCOUNT (2025): {plays_2025:,}")
    print(f"BESTSCORES: {len(scores_2025)}")
    
    if monthly_2025_data:
        print(f"\n[MONTHLY PLAYCOUNT (2025)]")
        print("-" * 80)
        for month_info in monthly_2025_data:
            print(f"  {month_info['month']}: {month_info['count']:,} plays")
    
    print("\n" + "=" * 80)
    print("[完了] osu! 2025 Wrapped")


def main():
    """メイン処理"""
    
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='osu! 2025 Wrapped - 2025年のプレイ統計を取得')
    parser.add_argument('username', nargs='?', help='osu! ユーザー名')
    args = parser.parse_args()
    
    # 環境変数から認証情報を取得
    client_id, client_secret = get_osu_credentials()
    
    if not client_id or not client_secret:
        print("[ERROR] OSU_CLIENT_ID と OSU_CLIENT_SECRET を .env ファイルに設定してください。")
        print("        config.example.txt を参考にしてください。")
        return
    
    # ユーザー名の取得
    if args.username:
        username = args.username
    else:
        # 引数がない場合は入力を求める
        try:
            username = input("osu! ユーザー名を入力してください: ").strip()
        except EOFError:
            print("\n[ERROR] ユーザー名を引数で指定してください: python main.py <ユーザー名>")
            return
    
    if not username:
        print("[ERROR] ユーザー名が入力されていません。")
        return
    
    try:
        get_2025_stats(username, client_id, client_secret)
    except requests.exceptions.HTTPError as e:
        print(f"\n[ERROR] APIエラーが発生しました: {e}")
        if e.response.status_code == 401:
            print("        認証に失敗しました。CLIENT_IDとCLIENT_SECRETを確認してください。")
    except Exception as e:
        print(f"\n[ERROR] エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
