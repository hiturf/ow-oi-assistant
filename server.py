"""OI助手OpenAPI服务器模块 - 支持OpenWebUI外部工具调用。"""

import hashlib
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from runner import CodeRunner
from security import SecurityManager


# ============== 请求/响应模型定义 ============== #

class CompileAndRunRequest(BaseModel):
    """编译运行C++代码的请求参数。"""
    code: str = Field(
        ...,
        description="要编译的C++源代码",
        examples=["#include <iostream>\nint main() { return 0; }"]
    )
    input: str = Field(
        ...,
        description="程序的标准输入数据",
        examples=["5 3"]
    )
    expected_output: Optional[str] = Field(
        None,
        description="预期输出，用于验证程序正确性（可选）"
    )
    filename: Optional[str] = Field(
        None,
        description="源文件名（可选，默认自动生成）"
    )
    time_limit: Optional[int] = Field(
        None,
        description="运行时间限制，单位毫秒（可选，默认5000ms）"
    )
    memory_limit: Optional[int] = Field(
        None,
        description="内存限制，单位MB（可选，默认256MB）"
    )


class CompileAndRunResponse(BaseModel):
    """编译运行的响应结果。"""
    success: bool = Field(description="操作是否成功")
    result: str = Field(description="详细结果报告（Markdown格式）")
    compile_success: Optional[bool] = Field(None, description="编译是否成功")
    run_success: Optional[bool] = Field(None, description="运行是否成功")
    output: Optional[str] = Field(None, description="程序输出")
    time_used: Optional[int] = Field(None, description="运行耗时（毫秒）")
    memory_used: Optional[int] = Field(None, description="内存使用（KB）")


class DebugRequest(BaseModel):
    """GDB调试请求参数。"""
    code: str = Field(
        ...,
        description="要调试的C++源代码"
    )
    gdb_script: Optional[str] = Field(
        None,
        description="GDB调试脚本（可选，默认自动设置断点并运行）"
    )


class DebugResponse(BaseModel):
    """GDB调试的响应结果。"""
    success: bool = Field(description="调试是否成功")
    result: str = Field(description="调试报告（Markdown格式）")
    gdb_output: Optional[str] = Field(None, description="GDB原始输出")


class CompareRequest(BaseModel):
    """输出比较请求参数。"""
    actual: str = Field(..., description="实际输出")
    expected: str = Field(..., description="预期输出")
    ignore_whitespace: bool = Field(
        True,
        description="是否忽略空白字符差异"
    )
    ignore_case: bool = Field(
        False,
        description="是否忽略大小写差异"
    )


class CompareResponse(BaseModel):
    """输出比较的响应结果。"""
    success: bool = Field(description="输出是否匹配")
    result: str = Field(description="比较报告（Markdown格式）")
    match_result: bool = Field(description="实际输出是否与预期匹配")
    differences: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="差异详情列表"
    )


class TestCaseRequest(BaseModel):
    """测试用例读取请求参数。"""
    test_case_id: str = Field(
        ...,
        description="测试用例ID，如 'a+b' 或 'fibonacci'"
    )


class TestCaseResponse(BaseModel):
    """测试用例的响应结果。"""
    success: bool = Field(description="是否成功获取测试用例")
    result: str = Field(description="测试用例内容（Markdown格式）")
    input_data: Optional[str] = Field(None, description="测试输入数据")
    expected_output: Optional[str] = Field(None, description="预期输出")
    description: Optional[str] = Field(None, description="测试用例描述")


class ChatMessage(BaseModel):
    """聊天消息。"""
    role: str = Field(description="消息角色: system/user/assistant")
    content: str = Field(description="消息内容")


class ChatCompletionRequest(BaseModel):
    """聊天补全请求（OpenAI兼容）。"""
    model: str = Field(default="oi-assistant", description="模型名称")
    messages: List[ChatMessage] = Field(description="对话消息列表")
    temperature: Optional[float] = Field(1.0, description="生成温度")


class ChatCompletionChoice(BaseModel):
    """聊天补全选项。"""
    index: int = Field(description="选项索引")
    message: ChatMessage = Field(description="生成的消息")
    finish_reason: str = Field(description="结束原因")


class ChatCompletionResponse(BaseModel):
    """聊天补全响应（OpenAI兼容）。"""
    id: str = Field(description="响应ID")
    object: str = Field(default="chat.completion", description="对象类型")
    created: int = Field(description="创建时间戳")
    model: str = Field(description="使用的模型")
    choices: List[ChatCompletionChoice] = Field(description="生成的选项列表")


# ============== FastAPI应用配置 ============== #

app = FastAPI(
    title="OI助手 - 竞赛编程工具集",
    description=(
        "OI助手提供C++代码编译、运行、调试和测试功能。\n\n"
        "## 使用方式\n"
        "1. 使用 compile_and_run 工具编译运行C++代码\n"
        "2. 使用 debug_with_gdb 工具调试程序\n"
        "3. 使用 compare_outputs 工具比较输出\n"
        "4. 使用 read_test_case 工具读取测试用例\n\n"
        "## OpenWebUI集成\n"
        "在OpenWebUI中添加外部工具，填入此服务的地址即可使用。"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    servers=[
        {"url": "http://localhost:8000", "description": "本地开发服务器"}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

runner: CodeRunner = CodeRunner()
security: SecurityManager = SecurityManager()
sessions: Dict[str, Dict[str, Any]] = {}


def _generate_session_id(prefix: str, data: str) -> str:
    """生成唯一会话ID。"""
    ts = int(time.time())
    h = hashlib.md5(data.encode()).hexdigest()[:8]
    return f"{prefix}_{ts}_{h}"


# ============== 工具API端点 ============== #

@app.post(
    "/tools/compile_and_run",
    response_model=CompileAndRunResponse,
    summary="编译并运行C++代码",
    description=(
        "编译C++源代码并在沙箱环境中运行。"
        "支持设置时间和内存限制，可自动比较输出结果。"
        "适用于OI/ACM竞赛编程练习。"
    ),
    tags=["工具"]
)
async def compile_and_run(request: CompileAndRunRequest) -> CompileAndRunResponse:
    """编译并运行C++代码。"""
    session_id = _generate_session_id("session", str(request.model_dump()))
    sessions[session_id] = {
        "start_time": time.time(),
        "tool": "compile_and_run",
        "arguments": request.model_dump(),
    }

    filename = request.filename or f"program_{session_id}"
    expected_output = request.expected_output or ""

    # 编译
    compile_result = runner.compile_cpp(request.code, filename)
    if not compile_result["success"]:
        error_msg = str(compile_result.get("error", "编译失败"))
        return CompileAndRunResponse(
            success=False,
            result=f"## 编译失败\n```\n{error_msg}\n```",
            compile_success=False
        )

    # 运行
    run_result = runner.run_with_input(
        compile_result["executable"],
        request.input,
        request.time_limit,
        request.memory_limit,
    )

    # 构建结果
    status = "成功" if run_result.get("success") else "失败"
    result_lines = [
        "## 编译运行报告",
        f"会话ID: {session_id}",
        f"文件: {filename}.cpp",
        "",
        "### 编译结果",
        "编译成功",
        "",
        "### 运行结果",
        f"状态: {status}",
        f"耗时: {run_result.get('time_used')}ms",
        f"内存: {run_result.get('memory_used')}KB",
    ]

    if run_result.get("output"):
        result_lines.extend(["", "### 程序输出", "```", run_result["output"], ""])
    if run_result.get("error"):
        result_lines.extend(["### 错误输出", "```", run_result["error"], ""])

    # 输出比较
    match_result = True
    if expected_output:
        compare_res = runner.compare_outputs(
            run_result.get("output", ""), expected_output
        )
        match_result = compare_res["match"]
        compare_status = "匹配" if match_result else "不匹配"
        result_lines.extend(["", "### 输出比较", f"结果: {compare_status}"])

    sessions.pop(session_id, None)

    return CompileAndRunResponse(
        success=run_result.get("success", False) and match_result,
        result="\n".join(result_lines),
        compile_success=True,
        run_success=run_result.get("success"),
        output=run_result.get("output"),
        time_used=run_result.get("time_used"),
        memory_used=run_result.get("memory_used"),
    )


@app.post(
    "/tools/debug_with_gdb",
    response_model=DebugResponse,
    summary="GDB调试C++程序",
    description=(
        "使用GDB调试C++程序。"
        "自动编译代码并启动GDB调试，可自定义调试脚本。"
        "默认自动在main函数设置断点并运行。"
    ),
    tags=["工具"]
)
async def debug_with_gdb(request: DebugRequest) -> DebugResponse:
    """使用GDB调试C++程序。"""
    session_id = _generate_session_id("debug", str(request.model_dump()))

    compile_result = runner.compile_cpp(request.code, f"debug_{session_id}")
    if not compile_result["success"]:
        return DebugResponse(
            success=False,
            result=f"## 编译失败\n```\n{compile_result.get('error')}\n```"
        )

    gdb_result = runner.run_gdb(
        compile_result["executable"],
        request.gdb_script
    )

    status = "成功" if gdb_result["success"] else "失败"
    result_lines = [
        "## GDB调试报告",
        f"状态: {status}",
    ]
    if gdb_result.get("output"):
        result_lines.extend(["", "### GDB输出", "```", gdb_result["output"], ""])

    return DebugResponse(
        success=gdb_result["success"],
        result="\n".join(result_lines),
        gdb_output=gdb_result.get("output")
    )


@app.post(
    "/tools/compare_outputs",
    response_model=CompareResponse,
    summary="比较程序输出",
    description=(
        "比较实际输出与预期输出。"
        "支持忽略空白字符和大小写差异。"
        "返回详细的差异列表。"
    ),
    tags=["工具"]
)
async def compare_outputs(request: CompareRequest) -> CompareResponse:
    """比较两个输出。"""
    result = runner.compare_outputs(
        request.actual,
        request.expected,
        request.ignore_whitespace,
        request.ignore_case,
    )

    match_status = "匹配" if result["match"] else "不匹配"
    result_lines = [
        "## 输出比较结果",
        f"结果: {match_status}",
        f"实际行数: {result['actual_line_count']}",
        f"预期行数: {result['expected_line_count']}",
    ]

    if not result["match"] and result.get("differences"):
        result_lines.append("\n### 差异详情")
        for diff in result["differences"][:10]:
            result_lines.extend([
                f"第{diff['line']}行:",
                f"  实际: {diff['actual']}",
                f"  预期: {diff['expected']}",
            ])

    return CompareResponse(
        success=result["match"],
        result="\n".join(result_lines),
        match_result=result["match"],
        differences=result.get("differences")
    )


@app.post(
    "/tools/read_test_case",
    response_model=TestCaseResponse,
    summary="读取测试用例",
    description=(
        "读取预定义或自定义的测试用例。"
        "内置测试用例: a+b, fibonacci。"
        "也可以读取自定义测试文件。"
    ),
    tags=["工具"]
)
async def read_test_case(request: TestCaseRequest) -> TestCaseResponse:
    """读取测试用例。"""
    safe_id = security.sanitize_filename(request.test_case_id)

    # 内置测试用例
    sample_cases = {
        "a+b": {
            "input": "3 5\n",
            "output": "8\n",
            "description": "A+B问题 - 计算两个整数的和"
        },
        "fibonacci": {
            "input": "10\n",
            "output": "55\n",
            "description": "斐波那契数列 - 求第n项"
        },
    }

    if safe_id in sample_cases:
        case = sample_cases[safe_id]
        return TestCaseResponse(
            success=True,
            result=(
                f"## 测试用例: {request.test_case_id}\n"
                f"描述: {case['description']}\n"
                f"输入: `{case['input'].strip()}`\n"
                f"输出: `{case['output'].strip()}`"
            ),
            input_data=case["input"],
            expected_output=case["output"],
            description=case["description"]
        )

    # 自定义测试文件
    test_file = security.temp_dir / "tests" / f"{safe_id}.txt"
    try:
        if test_file.exists():
            content = test_file.read_text(encoding="utf-8")
            return TestCaseResponse(
                success=True,
                result=f"## 测试用例文件: {request.test_case_id}\n```\n{content}\n```",
                input_data=content
            )
        return TestCaseResponse(
            success=False,
            result=f"未找到测试用例: {request.test_case_id}"
        )
    except (IOError, OSError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"读取失败: {str(exc)}"
        ) from exc


# ============== OpenAI兼容端点 ============== #

@app.get("/v1/models", tags=["OpenAI兼容"])
async def list_models() -> Dict[str, Any]:
    """列出可用模型（OpenAI兼容）。"""
    return {
        "object": "list",
        "data": [{
            "id": "oi-assistant",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "oi-assistant"
        }]
    }


@app.post(
    "/v1/chat/completions",
    response_model=ChatCompletionResponse,
    tags=["OpenAI兼容"]
)
async def chat_completions(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """聊天补全（OpenAI兼容）。"""
    user_message = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_message = msg.content
            break

    response_text = (
        f"OI助手收到您的请求: {user_message}\n\n"
        "请使用以下工具进行操作:\n"
        "- compile_and_run: 编译运行C++代码\n"
        "- debug_with_gdb: GDB调试\n"
        "- compare_outputs: 比较输出\n"
        "- read_test_case: 读取测试用例"
    )

    return ChatCompletionResponse(
        id=f"chatcmpl-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}",
        created=int(time.time()),
        model=request.model,
        choices=[ChatCompletionChoice(
            index=0,
            message=ChatMessage(role="assistant", content=response_text),
            finish_reason="stop"
        )]
    )


# ============== 系统端点 ============== #

@app.get("/health", tags=["系统"])
async def health_check() -> Dict[str, str]:
    """健康检查。"""
    return {"status": "healthy", "service": "oi-assistant"}


@app.get("/", tags=["系统"])
async def root() -> Dict[str, Any]:
    """API信息。"""
    return {
        "service": "OI助手",
        "version": "1.0.0",
        "description": "竞赛编程工具集 - 支持OpenWebUI外部工具调用",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "tools": [
            {"name": "compile_and_run", "path": "/tools/compile_and_run"},
            {"name": "debug_with_gdb", "path": "/tools/debug_with_gdb"},
            {"name": "compare_outputs", "path": "/tools/compare_outputs"},
            {"name": "read_test_case", "path": "/tools/read_test_case"},
        ]
    }
