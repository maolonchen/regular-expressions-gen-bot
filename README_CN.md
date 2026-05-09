# RegAgent - 基于大模型的正则表达式智能生成服务

RegAgent 是一个由大语言模型驱动的正则表达式生成服务。它接收自然语言描述的模式匹配需求，通过迭代方式生成并优化正则表达式，同时在样本输入上进行验证，直到得到正确的结果。

## 特性

- **自然语言生成正则**：用自然语言描述匹配需求即可生成对应的正则表达式
- **迭代优化**：通过最多 20 轮 LLM 反馈自动修正失败的正则
- **多样本验证**：支持主样本、补充样本和反例验证
- **安全控制**：执行超时限制、正则长度限制和匹配数量上限
- **模型无关**：兼容任何 OpenAI 格式的 Chat Completions API
- **高准确率**：在 63 个测试用例（覆盖 13+ 类别）上达到 **92%+ 准确率**

## 架构流程

```
用户请求（自然语言 + 样本）
        │
        ▼
   ┌─────────────┐
   │  调用 LLM   │ ◄── 生成初始正则表达式
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │   验证结果   │ ◄── 使用 re.finditer 在样本上测试
   └──────┬──────┘
          │
    ┌─────┴─────┐
    │  结果正确? │
    └─────┬─────┘
     否   │   是
     │    │    │
     ▼    │    ▼
  错误报告 │  最终检查 ──► LLM 确认
     │    │                    │
     └────►┤              ┌────┴────┐
           │              │  正确   │ ──► 返回结果
           ▼              └─────────┘
     重试（最多 20 次）
```

## 快速开始

### 环境要求

- Python >= 3.10（在 3.13 上测试通过）
- [uv](https://docs.astral.sh/uv/) 包管理器

### 安装

```bash
# 克隆仓库
git clone <repo-url>
cd reg_agent_dev

# 安装依赖
uv sync
```

### 配置

运行前需设置以下环境变量：

| 环境变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `CHAT_MODEL_NAME` | 是 | - | LLM 模型名称 |
| `CHAT_MODEL_API_URL` | 是 | - | OpenAI 兼容的 API 地址 |
| `CHAT_API_KEY` | 是 | - | API 密钥 |
| `API_HOST` | 否 | `0.0.0.0` | 服务绑定地址 |
| `API_PORT` | 否 | `8765` | 服务绑定端口 |
| `MAX_CORRECTION_ATTEMPTS` | 否 | `20` | 最大修正轮次 |
| `MAX_EXECUTION_TIME` | 否 | `1.0` | 正则验证超时时间（秒） |
| `MAX_REGEX_LENGTH` | 否 | `1000` | 正则最大长度（字符数） |
| `DEBUG` | 否 | `false` | 开启调试日志 |

### 启动服务

```bash
# 直接启动
python run_server.py

# 或使用管理脚本
chmod +x manage.sh
./manage.sh start    # 启动服务
./manage.sh status   # 查看状态
./manage.sh logs     # 查看日志
./manage.sh stop     # 停止服务
./manage.sh restart  # 重启服务
```

## API 接口

### 生成正则表达式

```
POST /generate-regex
```

**请求体：**

```json
{
  "user_request": "提取所有邮箱地址",
  "sample_input": "请联系 support@example.com 或 sales@company.org",
  "expected_matches": ["support@example.com", "sales@company.org"],
  "additional_examples": ["可选：更多示例字符串"],
  "negative_examples": ["可选：不应匹配的字符串"]
}
```

**成功响应：**

```json
{
  "success": true,
  "regex": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}",
  "matches": ["support@example.com", "sales@company.org"],
  "attempts": 3,
  "error": null
}
```

**失败响应：**

```json
{
  "success": false,
  "regex": "",
  "matches": [],
  "attempts": 20,
  "error": "经过 20 次尝试后仍未能生成正确的正则表达式"
}
```

### 健康检查

```
GET /health
```

返回 `{"status": "healthy", "llm_provider": "<模型名称>"}`。

## 准确率测试

运行基准测试：

```bash
python scripts/test_accuracy.py
```

该脚本对 63 个测试用例进行评估，覆盖邮箱、手机号、日期、IPv4 地址、URL、信用卡号、十六进制颜色、标签、浮点数等多个类别。

## 项目结构

```
reg_agent_dev/
├── main.py                  # FastAPI 应用入口
├── run_server.py            # Uvicorn 服务启动器
├── manage.sh                # 服务生命周期管理脚本
├── pyproject.toml           # 依赖与项目元信息
├── app/
│   ├── algorithms/
│   │   └── regex_agent.py   # 核心：迭代式正则生成 Agent
│   ├── api/
│   │   └── llm_api.py       # LLM API 客户端（OpenAI 兼容格式）
│   ├── conf/
│   │   ├── config.py        # 基于环境变量的配置
│   │   └── prompts.py       # 提示词模板（已加入 .gitignore）
│   ├── schemas/
│   │   └── re_schemas.py    # Pydantic 请求/响应模型
│   └── utils/
│       └── log_utils.py     # 日志工具（控制台 + 文件输出）
├── scripts/
│   └── test_accuracy.py     # 准确率基准测试脚本
└── data/
    └── test_data.json       # 63 个测试用例（13+ 类别）
```

## 许可证

MIT
