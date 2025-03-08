# PDF Term Extractor

这个 Python 工具可以从中英文对照的 PDF 文件中提取专业术语，并保存到 CSV 文件中。它利用 AWS Bedrock 中的 Claude 大语言模型（Claude 3.5 Sonnet v2、Claude 3.7 以及 Nova 系列模型）来识别和提取专业术语对。

## 功能特点

- 从中英文 PDF 文件中提取文本内容
- 利用 AWS Bedrock 中的 Claude 模型分析文本并提取专业术语对
- 提取的术语包含序号、中文术语和英文术语
- 将结果保存为 CSV 格式，支持 Excel 兼容的 UTF-8 编码

## 系统要求

- Python 3.8+
- AWS 账户，并配置了 Bedrock 访问权限
- 支持 Claude 模型（Claude 3.5 Sonnet v2、Claude 3.7、Nova 系列等）的区域

## 安装

1. 克隆或下载此仓库

2. 安装依赖包:
```bash
cd pdf-term-extractor
pip install -r requirements.txt
```

## 配置

1. 复制 `.env.example` 文件并重命名为 `.env`:
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入您的 AWS 凭证信息:
```
AWS_ACCESS_KEY_ID=your_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
AWS_REGION=us-east-1  # 改成您的 AWS 区域，确保该区域支持 Bedrock 和 Claude 模型
```

## 使用方法

### 命令行用法

基本用法:

```bash
python main.py -c chinese_doc.pdf -e english_doc.pdf -o terminology.csv
```

### 图形界面用法

我们也提供了基于 Gradio 的交互式 Web 界面：

```bash
python gradio_app.py
```

Web 界面提供以下功能：
- 上传中英文 PDF 文件
- 选择 AI 模型
- 自定义提示词模板
- 术语提取结果预览
- CSV 文件导出
- 实时处理日志

参数说明:
- `-c, --chinese-pdf`: 中文 PDF 文件路径（必需）
- `-e, --english-pdf`: 英文 PDF 文件路径（必需）
- `-o, --output`: 输出 CSV 文件路径（默认: terminology.csv）
- `-m, --model`: 使用的 AWS Bedrock Claude 模型（默认: anthropic.claude-3-5-sonnet-20241022-v2:0）

可选模型包括:
- `anthropic.claude-3-5-sonnet-20240620-v1:0`
- `anthropic.claude-3-5-sonnet-20241022-v2:0`（默认）
- `anthropic.claude-3-7-sonnet-20240620-v1:0`
- `anthropic.claude-3-opus-20240229-v1:0`
- `amazon.nova-lite-v1:0`
- `amazon.nova-pro-v1:0`

示例:
```bash
# 使用默认模型
python main.py -c docs/technical_manual_zh.pdf -e docs/technical_manual_en.pdf -o output/terms.csv

# 指定使用 Claude 3.7 模型
python main.py -c docs/technical_manual_zh.pdf -e docs/technical_manual_en.pdf -m anthropic.claude-3-7-sonnet-20240620-v1:0
```

## 输出格式

生成的 CSV 文件包含以下列:
- `name`: 术语序号
- `ZH_CN`: 中文术语
- `EN_US`: 对应的英文术语

## 项目结构

```
pdf-term-extractor/
├── main.py                # 主程序入口
├── requirements.txt       # 依赖包列表
├── .env.example           # 环境变量示例文件
├── README.md              # 项目说明文档
└── src/
    ├── __init__.py        # 包初始化文件
    ├── pdf_processor.py   # PDF 文本提取模块
    ├── bedrock_client.py  # AWS Bedrock API 客户端
    └── term_extractor.py  # 术语提取和保存模块
```

## 故障排除

### 常见问题

1. **AWS 认证错误**:
   - 确保您的 AWS 凭证正确，并且具有调用 Bedrock API 的权限
   - 验证 `.env` 文件中的 AWS_REGION 是否支持 Bedrock 和 Claude 模型

2. **PDF 提取问题**:
   - 确保 PDF 文件可读取且未加密
   - 如果 PDF 是扫描文档，可能需要先通过 OCR 工具处理

3. **内容过长错误**:
   - Claude 模型有上下文长度限制，如果 PDF 文件过大，程序会自动截取前 50,000 字符
   - 对于大型文档，建议拆分成多个小文件处理

### 日志

程序运行时会生成详细日志，可以帮助识别问题。默认级别为 INFO，可以在 `main.py` 中修改日志级别以获取更详细的信息。

## 授权

本项目仅供学习和研究使用。使用 AWS Bedrock 服务会产生相应费用，请参考 AWS 官方定价。
