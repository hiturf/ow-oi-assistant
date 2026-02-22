# OI助手 - OpenAPI版本

一个为编程竞赛（OI/ACM）选手设计的OpenAPI服务，可通过OpenWebUI等平台作为外部工具调用，支持安全地编译、运行和测试C++代码。

## 📋 功能列表

### 核心功能
- **编译运行C++代码**：一键编译并运行，支持时间和内存限制
- **GDB调试**：自动编译并启动GDB调试
- **输出比较**：对比实际输出与预期输出，显示差异详情
- **测试用例管理**：内置示例测试用例，支持自定义测试文件

### 安全特性
- **目录隔离**：所有文件操作限制在 `./tmp/` 目录内
- **命令过滤**：阻止执行危险系统命令
- **资源限制**：自动限制运行时间、内存和输出大小
- **文件名消毒**：防止路径遍历攻击

## 🛠️ 环境要求

| 组件 | 说明 |
|------|------|
| Python | 3.8+ |
| C++编译器 | [MinGW-w64](https://www.mingw-w64.org/) |

### MinGW安装
1. 下载 [MinGW-w64](https://www.mingw-w64.org/downloads/)
2. 解压后将文件夹命名为 `mingw64` 放在项目目录下
3. 确保 `mingw64/bin/g++.exe` 和 `mingw64/bin/gdb.exe` 存在

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动服务
```bash
python main.py
```

服务将在 `http://127.0.0.1:8000` 启动

### 环境变量配置
| 变量 | 默认值 | 说明 |
|------|--------|------|
| OI_HOST | 127.0.0.1 | 服务地址 |
| OI_PORT | 8000 | 服务端口 |

```bash
# 示例：自定义端口启动
OI_PORT=8080 python main.py
```

## 🔗 OpenWebUI集成

### 配置步骤

1. **启动OI助手服务**
   ```bash
   python main.py
   ```

2. **在OpenWebUI中添加外部工具**
   - 打开 OpenWebUI → 设置 → 工具
   - 点击「添加外部工具」
   - 填入服务地址：`http://localhost:8000`
   - OpenWebUI会自动读取 `/openapi.json` 识别可用工具

3. **使用工具**
   - 在对话中直接请求编译运行代码
   - OpenWebUI会自动调用相应的工具

### 可用工具

| 工具名称 | 功能 | 参数 |
|----------|------|------|
| compile_and_run | 编译运行C++代码 | code, input, expected_output, time_limit, memory_limit |
| debug_with_gdb | GDB调试 | code, gdb_script |
| compare_outputs | 比较输出 | actual, expected, ignore_whitespace, ignore_case |
| read_test_case | 读取测试用例 | test_case_id |

### OpenWebUI链接
- 官网：[https://openwebui.com](https://openwebui.com)
- GitHub：[https://github.com/open-webui/open-webui](https://github.com/open-webui/open-webui)
- 文档：[https://docs.openwebui.com](https://docs.openwebui.com)

## 📚 API文档

启动服务后访问：
- Swagger UI：`http://localhost:8000/docs`
- ReDoc：`http://localhost:8000/redoc`
- OpenAPI规范：`http://localhost:8000/openapi.json`

## 📁 目录结构

```
ow-oi-assistant/
├── main.py              # 启动入口
├── server.py            # OpenAPI服务器
├── runner.py            # 代码运行器
├── security.py          # 安全模块
├── config.yaml          # 配置文件
├── requirements.txt     # Python依赖
├── tmp/                 # 临时工作区（自动创建）
└── mingw64/             # MinGW工具链（需自行放置）
    └── bin/
        ├── g++.exe      # C++编译器
        └── gdb.exe      # 调试器
```

## ⚙️ 配置文件

`config.yaml` 主要配置项：

```yaml
# 安全设置
security:
  forbidden_commands:
    - "rm -rf"
    - "format"
    - "del"
    
# 编译设置
compilation:
  compiler_path: "./mingw64/bin/g++.exe"
  cpp_standard: "c++17"
  optimization_level: "-O2"

# 运行限制
execution:
  max_time: 5000           # 最大运行时间（毫秒）
  max_memory: 256          # 最大内存（MB）
  max_output_size: 1048576 # 最大输出（1MB）

# 路径设置
paths:
  temp_dir: "./tmp"
  mingw_dir: "./mingw64"
```

## 🔧 API端点

### 工具API

```
POST /tools/compile_and_run  # 编译运行C++代码
POST /tools/debug_with_gdb   # GDB调试
POST /tools/compare_outputs  # 输出比较
POST /tools/read_test_case   # 读取测试用例
```

### OpenAI兼容API

```
GET  /v1/models              # 模型列表
POST /v1/chat/completions    # 聊天补全
```

### 系统端点

```
GET  /health                 # 健康检查
GET  /                       # API信息
```

## 📝 内置测试用例

| ID | 描述 | 输入 | 输出 |
|----|----|------|------|
| a+b | A+B问题 | 3 5 | 8 |
| fibonacci | 斐波那契数列第n项 | 10 | 55 |

## 📄 许可证

MIT License
