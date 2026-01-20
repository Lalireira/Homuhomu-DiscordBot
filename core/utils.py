#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ユーティリティ関数モジュール"""

from typing import List, Dict
from core.osu_api import OsuAPIClient


def format_mods(mods: List[str]) -> str:
    """MODSを見やすくフォーマット"""
    if not mods:
        return "NoMod"
    return "+".join(mods)


def calculate_modded_star_rating(base_star_rating: float, mods: List[str]) -> float:
    """MOD適用後のStar Ratingを計算（フォールバック用）"""
    if not mods or base_star_rating == 0:
        return base_star_rating
    
    modded_sr = base_star_rating
    
    # MODの倍率（osu!標準の計算式に基づく近似値）
    mod_multipliers = {
        'HR': 1.08,   # Hard Rock
        'DT': 1.12,   # Double Time
        'NC': 1.12,   # Nightcore (DTと同じ)
        'EZ': 0.5,    # Easy
        'HT': 0.3,    # Half Time
    }
    
    # MODの組み合わせ処理
    has_dt = 'DT' in mods or 'NC' in mods
    has_ht = 'HT' in mods
    has_ez = 'EZ' in mods
    has_hr = 'HR' in mods
    
    # EZとHTは同時に適用できない（通常はEZが優先）
    if has_ez:
        modded_sr *= 0.5
    elif has_ht:
        modded_sr *= 0.3
    
    # DT/NCはHTと同時に適用できない（DT/NCが優先）
    if has_dt and not has_ht:
        modded_sr *= 1.12
    
    # HRは他のMODと組み合わせ可能
    if has_hr:
        modded_sr *= 1.08
    
    return modded_sr


def get_modded_star_rating_from_api(score: Dict, client: OsuAPIClient) -> float:
    """APIからMOD適用後のStar Ratingを取得"""
    try:
        beatmap = score.get('beatmap', {})
        beatmap_id = beatmap.get('id')
        mods_list = score.get('mods', [])
        
        if not beatmap_id:
            # フォールバック: 計算による取得
            base_sr = beatmap.get('difficulty_rating', 0)
            return calculate_modded_star_rating(base_sr, mods_list)
        
        # APIからMOD適用後の属性を取得
        attributes = client.get_beatmap_attributes(beatmap_id, mods_list)
        
        if attributes and 'attributes' in attributes:
            star_rating = attributes['attributes'].get('star_rating', 0)
            if star_rating > 0:
                return star_rating
        
        # フォールバック: 計算による取得
        base_sr = beatmap.get('difficulty_rating', 0)
        return calculate_modded_star_rating(base_sr, mods_list)
        
    except Exception as e:
        # エラー時は計算による取得にフォールバック
        beatmap = score.get('beatmap', {})
        base_sr = beatmap.get('difficulty_rating', 0)
        mods_list = score.get('mods', [])
        return calculate_modded_star_rating(base_sr, mods_list)

