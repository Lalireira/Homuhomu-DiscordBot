#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ロギング設定モジュール"""

import logging
import sys
from typing import Optional


def setup_logger(name: str = "bot", level: int = logging.INFO) -> logging.Logger:
    """ロガーをセットアップして返す"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 既にハンドラーが設定されている場合は追加しない
    if logger.handlers:
        return logger
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # フォーマッター: 日時 レベル [機能名] メッセージ (discordライブラリと統一)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)-8s %(name)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """機能ごとのロガーを取得（既存のロガーがない場合は作成）"""
    return logging.getLogger(name) if logging.getLogger(name).handlers else setup_logger(name)

