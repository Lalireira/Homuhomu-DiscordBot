#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""osu! 2025 Wrapped コマンド定義モジュール"""

import discord
from discord import app_commands
from typing import Optional
from core.config import get_osu_credentials
from core.utils import format_mods
from core.logger import get_logger
from .data import get_2025_stats_data
from .embeds import create_wrapped_embed

logger = get_logger("wrapped")


async def wrapped_command_handler(interaction: discord.Interaction, username: str):
    """osu! 2025 Wrappedコマンドハンドラ"""
    import json
    import time
    debug_log_path = r"c:\Users\Reira\Documents\git_repository\osu2025-wrapped\.cursor\debug.log"
    
    # #region agent log
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "commands.py:19", "message": "Handler entry", "data": {"username": username, "interaction_id": str(interaction.id), "response_is_done": interaction.response.is_done()}, "timestamp": int(time.time() * 1000)}) + "\n")
    except: pass
    # #endregion
    
    logger.info(f"コマンドリクエスト: username={username}, user_id={interaction.user.id}, guild_id={interaction.guild_id if interaction.guild_id else 'DM'}")
    
    # 認証情報の確認
    client_id, client_secret = get_osu_credentials()
    if not client_id or not client_secret:
        logger.error("osu! API認証情報が設定されていません")
        # #region agent log
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "commands.py:28", "message": "Credentials check failed", "data": {"username": username, "interaction_id": str(interaction.id)}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        await interaction.response.send_message(
            "❌ Error: osu! API credentials are not configured. Please contact the bot administrator.",
            ephemeral=True
        )
        return
    
    # 処理中メッセージを送信
    # #region agent log
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "commands.py:35", "message": "Before defer", "data": {"username": username, "interaction_id": str(interaction.id), "response_is_done": interaction.response.is_done()}, "timestamp": int(time.time() * 1000)}) + "\n")
    except: pass
    # #endregion
    
    # インタラクションが既に応答済みかチェック
    if interaction.response.is_done():
        # #region agent log
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "commands.py:40", "message": "Interaction already responded", "data": {"username": username, "interaction_id": str(interaction.id)}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        logger.warning(f"インタラクションは既に応答済み: username={username}")
        return
    
    try:
        await interaction.response.defer(thinking=True)
        # #region agent log
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "commands.py:48", "message": "After defer success", "data": {"username": username, "interaction_id": str(interaction.id)}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
    except discord.errors.NotFound as e:
        # #region agent log
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "commands.py:54", "message": "Defer failed - Unknown interaction", "data": {"username": username, "interaction_id": str(interaction.id), "error": str(e), "error_code": 10062}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        # インタラクションが既に期限切れまたは無効の場合、ユーザーに通知できない（インタラクションが無効なため）
        # この場合は静かに処理を終了する
        logger.warning(f"インタラクションが既にタイムアウトまたは無効: username={username}, error={e}")
        return
    except discord.errors.InteractionResponded as e:
        # #region agent log
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "commands.py:63", "message": "Defer failed - Already responded", "data": {"username": username, "interaction_id": str(interaction.id), "error": str(e)}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        logger.warning(f"インタラクションは既に応答済み: username={username}, error={e}")
        return
    except Exception as e:
        # #region agent log
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "commands.py:70", "message": "Defer failed - Other error", "data": {"username": username, "interaction_id": str(interaction.id), "error": str(e)}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        logger.error(f"deferエラー: username={username}, error={e}", exc_info=True)
        # deferに失敗した場合、通常の応答を試みる（ただし、これも失敗する可能性が高い）
        try:
            await interaction.response.send_message(
                "❌ An error occurred while processing your request. Please try again.",
                ephemeral=True
            )
        except:
            pass  # 応答も失敗した場合は何もしない
        return
    
    try:
        # 統計データを取得
        logger.info(f"osu! APIリクエスト開始: username={username}")
        # #region agent log
        api_start_time = time.time()
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "commands.py:54", "message": "Before get_2025_stats_data", "data": {"username": username, "interaction_id": str(interaction.id), "api_start_time": api_start_time}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        stats_data = get_2025_stats_data(username, client_id, client_secret)
        
        # #region agent log
        api_end_time = time.time()
        api_duration = api_end_time - api_start_time
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "commands.py:60", "message": "After get_2025_stats_data", "data": {"username": username, "interaction_id": str(interaction.id), "api_duration": api_duration, "stats_data_is_none": stats_data is None, "has_scores": stats_data is not None and len(stats_data.get('scores_2025', [])) > 0 if stats_data else False}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        if not stats_data:
            logger.warning(f"ユーザーが見つかりませんでした: username={username}")
            # #region agent log
            try:
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "commands.py:66", "message": "User not found", "data": {"username": username, "interaction_id": str(interaction.id)}, "timestamp": int(time.time() * 1000)}) + "\n")
            except: pass
            # #endregion
            await interaction.followup.send(
                f"❌ User '{username}' not found. Please check the username."
            )
            return
        
        # 2025年のスコアがなくても他の情報（プレイカウントなど）は表示する
        if not stats_data['scores_2025']:
            logger.info(f"2025年のベストスコアが見つかりませんでした（Top PPセクションは除外）: username={username}, user_id={stats_data['user']['id']}")
            # #region agent log
            try:
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "F", "location": "commands.py:103", "message": "No scores found", "data": {"username": username, "interaction_id": str(interaction.id), "user_id": stats_data['user']['id']}, "timestamp": int(time.time() * 1000)}) + "\n")
            except: pass
            # #endregion
        
        # Embedを作成して送信
        logger.info(f"データ取得成功: username={username}, user_id={stats_data['user']['id']}, scores_count={len(stats_data['scores_2025'])}, playcount_2025={stats_data['plays_2025']}")
        # #region agent log
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "G", "location": "commands.py:109", "message": "Before create_wrapped_embed", "data": {"username": username, "interaction_id": str(interaction.id), "scores_count": len(stats_data['scores_2025'])}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        embed = create_wrapped_embed(username, stats_data)
        
        # #region agent log
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "G", "location": "commands.py:115", "message": "Before followup.send", "data": {"username": username, "interaction_id": str(interaction.id)}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
        await interaction.followup.send(embed=embed)
        logger.info(f"コマンド成功: username={username}")
        
        # #region agent log
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "G", "location": "commands.py:122", "message": "After followup.send success", "data": {"username": username, "interaction_id": str(interaction.id)}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        
    except Exception as e:
        # #region agent log
        try:
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H", "location": "commands.py:97", "message": "Exception in handler", "data": {"username": username, "interaction_id": str(interaction.id), "error": str(e), "error_type": type(e).__name__}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        logger.error(f"wrappedコマンド失敗: username={username}, error={str(e)}", exc_info=True)
        try:
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}\nPlease try again."
            )
        except Exception as followup_error:
            # #region agent log
            try:
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H", "location": "commands.py:105", "message": "Followup.send also failed", "data": {"username": username, "interaction_id": str(interaction.id), "error": str(followup_error)}, "timestamp": int(time.time() * 1000)}) + "\n")
            except: pass
            # #endregion
            logger.error(f"followup.sendも失敗: username={username}, error={followup_error}", exc_info=True)


async def wrapped_simple_command_handler(interaction: discord.Interaction, username: str):
    """簡易版osu! 2025 Wrappedコマンドハンドラ"""
    logger.info(f"コマンドリクエスト: username={username}, user_id={interaction.user.id}, guild_id={interaction.guild_id if interaction.guild_id else 'DM'}")
    
    client_id, client_secret = get_osu_credentials()
    if not client_id or not client_secret:
        logger.error("osu! API認証情報が設定されていません")
        await interaction.response.send_message(
            "❌ Error: osu! API credentials are not configured.",
            ephemeral=True
        )
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        logger.info(f"osu! APIリクエスト開始: username={username}")
        stats_data = get_2025_stats_data(username, client_id, client_secret)
        
        if not stats_data:
            logger.warning(f"ユーザーが見つかりませんでした: username={username}")
            await interaction.followup.send(
                f"❌ User '{username}' not found."
            )
            return
        
        user = stats_data['user']
        plays_2025 = stats_data['plays_2025']
        top_10_scores = stats_data['top_10_scores']
        
        # 2025年のスコアがない場合はログに記録（Top PPセクションは除外される）
        if not stats_data['scores_2025']:
            logger.info(f"2025年のベストスコアが見つかりませんでした（プレイカウントのみ表示します）: username={username}, user_id={user['id']}")
        
        # 簡易Embed
        embed = discord.Embed(
            title=f"osu! 2025 Wrapped - {user['username']}",
            color=0xff1493
        )
        
        avatar_url = user.get('avatar_url', '')
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        
        embed.add_field(
            name="Statistics",
            value=f"**2025 Playcount:** {plays_2025:,}\n**Best Scores:** {len(stats_data['scores_2025'])}",
            inline=False
        )
        
        if top_10_scores:
            top_3_text = ""
            for i, score in enumerate(top_10_scores[:3], 1):
                pp = score.get('pp', 0)
                beatmapset = score.get('beatmapset', {})
                beatmap = score.get('beatmap', {})
                artist = beatmapset.get('artist', 'Unknown')
                title = beatmapset.get('title', 'Unknown')
                base_sr = beatmap.get('difficulty_rating', 0)
                mods_list = score.get('mods', [])
                modded_sr = score.get('_modded_star_rating', 0)
                if modded_sr == 0:
                    from core.utils import calculate_modded_star_rating
                    modded_sr = calculate_modded_star_rating(base_sr, mods_list)
                beatmapset_id = beatmapset.get('id', 0)
                beatmap_id = beatmap.get('id', 0)
                beatmap_url = f"https://osu.ppy.sh/beatmapsets/{beatmapset_id}#osu/{beatmap_id}" if beatmapset_id and beatmap_id else ""
                difficulty = beatmap.get('version', 'Unknown')
                song_diff_text = f"{artist} - {title} [{difficulty}]"
                if beatmap_url:
                    song_diff_text = f"[{song_diff_text}]({beatmap_url})"
                mods = format_mods(mods_list) if mods_list else "NoMod"
                mod_display = f" +{mods}" if mods != "NoMod" else ""
                top_3_text += f"**#{i}** {song_diff_text}\n{modded_sr:.2f}⭐ {pp:.2f}pp{mod_display}\n\n"
            embed.add_field(name="Top 3 PP", value=top_3_text, inline=False)
        
        logger.info(f"データ取得成功: username={username}, user_id={user['id']}, scores_count={len(stats_data['scores_2025'])}, playcount_2025={plays_2025}")
        await interaction.followup.send(embed=embed)
        logger.info(f"コマンド成功: username={username}")
        
    except Exception as e:
        logger.error(f"コマンド失敗: username={username}, error={str(e)}", exc_info=True)
        await interaction.followup.send(f"❌ Error: {str(e)}")

