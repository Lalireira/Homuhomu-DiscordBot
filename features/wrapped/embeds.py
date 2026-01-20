#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""osu! 2025 Wrapped Embed作成モジュール"""

from datetime import datetime
import discord
from core.utils import format_mods, calculate_modded_star_rating


def create_wrapped_embed(username: str, stats_data: dict) -> discord.Embed:
    """osu! 2025 WrappedのEmbedを作成"""
    user = stats_data['user']
    top_10_scores = stats_data['top_10_scores']
    plays_2025 = stats_data['plays_2025']
    monthly_2025_data = stats_data['monthly_2025_data']
    total_playcount = stats_data['total_playcount']
    
    # メインEmbed
    user_id = user['id']
    user_page_url = f"https://osu.ppy.sh/users/{user_id}"
    username = user['username']
    embed = discord.Embed(
        title=f"🎮 osu! 2025 Wrapped",
        color=0xff1493,  # ディープピンク
        description=f"[**{username}**]({user_page_url}) (ID: {user_id})"
    )
    
    # ユーザーアイコンを設定
    avatar_url = user.get('avatar_url', '')
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)
    
    # 統計情報（インラインで横並びに）
    embed.add_field(
        name="📊 Total Playcount",
        value=f"{total_playcount:,}",
        inline=True
    )
    embed.add_field(
        name="🎯 2025 Playcount",
        value=f"{plays_2025:,}",
        inline=True
    )
    embed.add_field(
        name="⭐ 2025 Best Scores",
        value=f"{len(stats_data['scores_2025'])}",
        inline=True
    )
    
    # 月別プレイカウント（最良月をハイライト）
    if monthly_2025_data:
        best_month = max(monthly_2025_data, key=lambda x: x['count'])
        monthly_text = f"**Peak:** {best_month['month']} - {best_month['count']:,} plays\n\n"
        # 月を縦に並べて表示
        for month_data in monthly_2025_data:
            monthly_text += f"• {month_data['month']}: {month_data['count']:,} plays\n"
        embed.add_field(name="📅 Monthly Playcount", value=monthly_text.strip(), inline=False)
    
    # トップ10 PPスコア（見やすくグループ化）
    if top_10_scores:
        # トップ3を1つのフィールドに
        top3_text = ""
        for i, score in enumerate(top_10_scores[:3], 1):
            beatmapset = score.get('beatmapset', {})
            beatmap = score.get('beatmap', {})
            pp = score.get('pp', 0)
            artist = beatmapset.get('artist', 'Unknown')
            title = beatmapset.get('title', 'Unknown')
            difficulty = beatmap.get('version', 'Unknown')
            mods_list = score.get('mods', [])
            mods = format_mods(mods_list)
            # APIから取得したMOD適用後のSRを使用（フォールバックとして計算値も利用可能）
            modded_star_rating = score.get('_modded_star_rating', 0)
            if modded_star_rating == 0:
                base_star_rating = beatmap.get('difficulty_rating', 0)
                modded_star_rating = calculate_modded_star_rating(base_star_rating, mods_list)
            
            beatmapset_id = beatmapset.get('id', 0)
            beatmap_id = beatmap.get('id', 0)
            beatmap_url = f"https://osu.ppy.sh/beatmapsets/{beatmapset_id}#osu/{beatmap_id}" if beatmapset_id and beatmap_id else ""
            
            song_diff_text = f"{artist} - {title} [{difficulty}]"
            if beatmap_url:
                song_diff_text = f"[{song_diff_text}]({beatmap_url})"
            
            mod_display = f" +{mods}" if mods != "NoMod" else ""
            top3_text += f"**#{i}** {song_diff_text}\n`{modded_star_rating:.2f}⭐` `{pp:.2f}pp`{mod_display}\n\n"
        
        embed.add_field(name="🏆 Top 10", value=top3_text.strip(), inline=False)
        
        # 4-6位を1つのフィールドに
        if len(top_10_scores) > 3:
            mid_text = ""
            for i, score in enumerate(top_10_scores[3:6], 4):
                beatmapset = score.get('beatmapset', {})
                beatmap = score.get('beatmap', {})
                pp = score.get('pp', 0)
                artist = beatmapset.get('artist', 'Unknown')
                title = beatmapset.get('title', 'Unknown')
                difficulty = beatmap.get('version', 'Unknown')
                mods_list = score.get('mods', [])
                mods = format_mods(mods_list)
                # APIから取得したMOD適用後のSRを使用（フォールバックとして計算値も利用可能）
                modded_star_rating = score.get('_modded_star_rating', 0)
                if modded_star_rating == 0:
                    base_star_rating = beatmap.get('difficulty_rating', 0)
                    modded_star_rating = calculate_modded_star_rating(base_star_rating, mods_list)
                
                beatmapset_id = beatmapset.get('id', 0)
                beatmap_id = beatmap.get('id', 0)
                beatmap_url = f"https://osu.ppy.sh/beatmapsets/{beatmapset_id}#osu/{beatmap_id}" if beatmapset_id and beatmap_id else ""
                
                song_diff_text = f"{artist} - {title} [{difficulty}]"
                if beatmap_url:
                    song_diff_text = f"[{song_diff_text}]({beatmap_url})"
                
                mod_display = f" +{mods}" if mods != "NoMod" else ""
                mid_text += f"**#{i}** {song_diff_text}\n`{modded_star_rating:.2f}⭐` `{pp:.2f}pp`{mod_display}\n\n"
            
            embed.add_field(name="\u200b", value=mid_text.strip(), inline=False)
        
        # 7-10位を1つのフィールドに
        if len(top_10_scores) > 6:
            bottom_text = ""
            for i, score in enumerate(top_10_scores[6:10], 7):
                beatmapset = score.get('beatmapset', {})
                beatmap = score.get('beatmap', {})
                pp = score.get('pp', 0)
                artist = beatmapset.get('artist', 'Unknown')
                title = beatmapset.get('title', 'Unknown')
                difficulty = beatmap.get('version', 'Unknown')
                mods_list = score.get('mods', [])
                mods = format_mods(mods_list)
                # APIから取得したMOD適用後のSRを使用（フォールバックとして計算値も利用可能）
                modded_star_rating = score.get('_modded_star_rating', 0)
                if modded_star_rating == 0:
                    base_star_rating = beatmap.get('difficulty_rating', 0)
                    modded_star_rating = calculate_modded_star_rating(base_star_rating, mods_list)
                
                beatmapset_id = beatmapset.get('id', 0)
                beatmap_id = beatmap.get('id', 0)
                beatmap_url = f"https://osu.ppy.sh/beatmapsets/{beatmapset_id}#osu/{beatmap_id}" if beatmapset_id and beatmap_id else ""
                
                song_diff_text = f"{artist} - {title} [{difficulty}]"
                if beatmap_url:
                    song_diff_text = f"[{song_diff_text}]({beatmap_url})"
                
                mod_display = f" +{mods}" if mods != "NoMod" else ""
                bottom_text += f"**#{i}** {song_diff_text}\n`{modded_star_rating:.2f}⭐` `{pp:.2f}pp`{mod_display}\n\n"
            
            embed.add_field(name="\u200b", value=bottom_text.strip(), inline=False)
    
    # フッターに日時を追加
    embed.timestamp = datetime.utcnow()
    embed.set_footer(text="ホムホム")
    
    return embed

