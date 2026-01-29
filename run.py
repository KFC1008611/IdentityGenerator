#!/usr/bin/env python
"""
直接运行入口 - 无需安装
用法: python run.py [options]
"""

import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from identity_gen.cli import main

if __name__ == "__main__":
    main()
