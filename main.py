#!/usr/bin/env python3
"""OI助手OpenAPI服务器启动入口。"""

import os
import sys

import uvicorn


def main() -> None:
    """主函数：检查目录并启动服务器。"""
    print("🚀 OI助手 OpenAPI 服务器 v1.0")
    print("=" * 50)

    # 检查必要目录
    required_dirs = ['tmp', 'mingw64/bin']
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"⚠️  警告: 目录 '{dir_path}' 不存在")
            if dir_path == 'mingw64/bin':
                print("请确保MinGW已安装并放置在mingw64目录中")

    # 获取配置
    host = os.environ.get("OI_HOST", "127.0.0.1")
    port = int(os.environ.get("OI_PORT", "8000"))

    print(f"\n📡 启动服务器: http://{host}:{port}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    print(f"📖 ReDoc文档: http://{host}:{port}/redoc")
    print(f"📋 OpenAPI规范: http://{host}:{port}/openapi.json")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 50)

    try:
        uvicorn.run(
            "server:app",
            host=host,
            port=port,
            reload=False,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except OSError as e:
        print(f"❌ 系统错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
