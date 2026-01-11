#!/usr/bin/env python
"""
检查配置是否正确加载
运行: python scripts/check_config.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings

def main():
    settings = get_settings()
    
    print("=" * 50)
    print("[Config Check]")
    print("=" * 50)
    
    # 检查 DeepSeek 配置
    print("\n[DeepSeek Moderation Config]:")
    print(f"  - MODERATION_ENABLED: {settings.MODERATION_ENABLED}")
    print(f"  - DEEPSEEK_API_URL: {settings.DEEPSEEK_API_URL}")
    print(f"  - DEEPSEEK_MODEL: {settings.DEEPSEEK_MODEL}")
    print(f"  - MODERATION_TIMEOUT: {settings.MODERATION_TIMEOUT}s")
    
    # API Key 检查（只显示部分，保护隐私）
    if settings.DEEPSEEK_API_KEY:
        key = settings.DEEPSEEK_API_KEY
        masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
        print(f"  - DEEPSEEK_API_KEY: {masked_key} [OK]")
    else:
        print(f"  - DEEPSEEK_API_KEY: [NOT SET] (moderation will be skipped)")
    
    print("\n" + "=" * 50)
    print("[Done]")
    print("=" * 50)

if __name__ == "__main__":
    main()
