#!/usr/bin/env python3
"""OI助手OpenAPI服务器启动入口。"""

import os
import sys

import uvicorn
import yaml


def load_config() -> dict:
    """加载配置文件。"""
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}


def main() -> None:
    """主函数：检查目录并启动服务器。"""
    print("OI助手 OpenAPI 服务器 v1.0")
    print("=" * 50)

    # 检查必要目录
    required_dirs = ["tmp", "mingw64/bin"]
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"警告: 目录 '{dir_path}' 不存在")
            if dir_path == "mingw64/bin":
                print("请确保MinGW已安装并放置在mingw64目录中")

    # 加载配置
    config = load_config()
    server_config = config.get("server", {})

    # 优先使用环境变量，其次使用配置文件
    host = os.environ.get("OI_HOST") or server_config.get("host", "127.0.0.1")
    port = int(os.environ.get("OI_PORT") or server_config.get("port", 8000))

    print(f"\n启动服务器: http://{host}:{port}")
    print(f"API文档: http://{host}:{port}/docs")
    print(f"ReDoc文档: http://{host}:{port}/redoc")
    print(f"OpenAPI规范: http://{host}:{port}/openapi.json")
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
        print("\n服务器已停止")
    except OSError as exc:
        print(f"系统错误: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
