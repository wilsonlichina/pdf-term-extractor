# PDF 专业术语提取器

这个 Python 应用提供交互式网页界面，可以从中英文对照的 PDF 文件中提取专业术语，并保存到 CSV 文件中。它基于 Gradio 框架开发，利用 AWS Bedrock 中的 Claude 大语言模型（Claude 3.5 Sonnet v2、Claude 3.7 以及 Nova 系列模型）来识别和提取专业术语对。

## 功能特点

1. **模型选择功能**：支持选择不同的 AWS Bedrock AI 处理模型
2. **文件上传区域**：左侧上传中文 PDF，右侧上传英文 PDF
3. **提取结果预览**：直观呈现识别到的专业术语
4. **提示词编辑功能**：允许用户自定义和优化提示词
5. **CSV 文件导出**：方便用户下载提取的术语表
6. **实时日志显示**：展示术语提取过程和状态信息

## 系统要求

- Python 3.8+
- AWS 账户，配置了 Bedrock 访问权限
- 支持 Claude 或 Nova 模型的 AWS 区域

## 安装与配置

### 方式一：本地安装

1. 克隆或下载此仓库
   ```bash
   git clone https://github.com/yourusername/pdf-term-extractor.git
   cd pdf-term-extractor
   ```

2. 安装依赖包:
   ```bash
   pip install -r requirements.txt
   ```

3. 配置 AWS 凭证:
   - 复制 `.env.example` 文件并重命名为 `.env`:
     ```bash
     cp .env.example .env
     ```
   - 编辑 `.env` 文件，填入您的 AWS 凭证信息:
     ```
     AWS_ACCESS_KEY_ID=your_access_key_id_here
     AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
     AWS_REGION=us-east-1  # 改成您的 AWS 区域，确保该区域支持 Bedrock 和所需模型
     ```

### 方式二：Docker 容器化部署

Docker 部署方案采用多阶段构建，优化了镜像大小并加强了安全性。支持通过环境变量或配置文件两种方式进行 AWS 认证配置。

#### 1. 构建 Docker 镜像

```bash
# 在项目根目录下执行构建
docker build -t pdf-term-extractor .
```

镜像构建特点：
- 采用多阶段构建，优化镜像大小
- 使用 Python 虚拟环境隔离依赖
- 集成安全加固措施
- 配置健康检查机制

#### 2. 运行容器

提供两种 AWS 认证配置方式：

##### 方式 A：使用环境变量（推荐用于测试环境）

```bash
docker run -d \
  --name pdf-extractor \
  -p 7860:7860 \
  -e AWS_ACCESS_KEY_ID=您的访问密钥ID \
  -e AWS_SECRET_ACCESS_KEY=您的访问密钥 \
  -e AWS_REGION=您的区域代码 \
  -v $(pwd)/glossary_files:/app/glossary_files \
  pdf-term-extractor
```

##### 方式 B：使用 AWS 凭证文件（推荐用于生产环境）

1. 准备 AWS 凭证文件：
   ```bash
   # 创建配置目录
   mkdir -p .aws
   
   # 复制示例配置文件
   cp aws-credentials.example .aws/credentials
   
   # 编辑凭证文件，填入您的 AWS 凭证信息
   vim .aws/credentials
   ```

2. 启动容器：
   ```bash
   docker run -d \
     --name pdf-extractor \
     -p 7860:7860 \
     -v $(pwd)/.aws:/app/.aws \
     -v $(pwd)/glossary_files:/app/glossary_files \
     pdf-term-extractor
   ```

#### 3. 容器管理命令

```bash
# 查看容器日志
docker logs pdf-extractor

# 停止容器
docker stop pdf-extractor

# 重启容器
docker restart pdf-extractor

# 删除容器
docker rm -f pdf-extractor
```

#### 4. 安全性说明

- 容器以非 root 用户运行，增强安全性
- AWS 凭证文件权限严格控制（700）
- 集成 Tini 作为初始化系统，确保进程管理
- 定期安全更新基础镜像

#### 5. 数据持久化

- glossary_files 目录自动挂载为数据卷
- 术语表 CSV 文件保存在宿主机，容器重启不会丢失
- 支持定期备份挂载目录数据

#### 6. 健康检查

- 内置自动健康检查机制
- 每 30 秒检查一次应用状态
- 支持容器编排系统的自动恢复

#### 7. 访问应用

容器启动后，通过浏览器访问：http://localhost:7860

所有功能与本地部署版本完全一致：
- 模型选择
- PDF 文件上传
- 术语提取预览
- 提示词编辑
- CSV 导出
- 日志显示

## 使用方法

启动 Gradio 交互式 Web 界面：

```bash
python gradio_app.py
```

应用启动后，您可以通过 Web 浏览器访问界面（默认地址为 http://127.0.0.1:7860）

### 使用步骤：

1. **上传 PDF 文件**：
   - 左侧上传中文 PDF 文件
   - 右侧上传对应的英文 PDF 文件

2. **选择 AI 模型**：
   从下拉菜单中选择要使用的 AWS Bedrock 模型，可选项包括：
   - `anthropic.claude-3-5-sonnet-20241022-v2:0`（默认）
   - `anthropic.claude-3-5-sonnet-20240620-v1:0`
   - `anthropic.claude-3-7-sonnet-20240620-v1:0`
   - `anthropic.claude-3-opus-20240229-v1:0`
   - `amazon.nova-lite-v1:0`
   - `amazon.nova-pro-v1:0`

3. **自定义提示词**（可选）：
   - 根据需要编辑提示词模板，以优化术语提取效果

4. **提取术语**：
   - 点击"提取专业术语"按钮开始处理

5. **查看结果**：
   - 处理完成后，右侧会显示提取到的术语表格
   - 界面底部会显示处理日志

6. **下载结果**：
   - 点击"下载术语表 CSV"按钮保存结果

## 输出结果格式

生成的 CSV 文件包含以下三列:
- `name`: 术语唯一标识（6位随机字符串）
- `ZH_CN`: 中文专业术语
- `EN_US`: 对应的英文专业术语

CSV 文件将自动保存在 `glossary_files` 目录下，文件名包含时间戳，方便区分不同批次的提取结果。

## 项目结构

```
pdf-term-extractor/
├── gradio_app.py          # Gradio Web 应用入口
├── requirements.txt       # 依赖包列表
├── .env.example           # 环境变量示例文件
├── README.md              # 项目说明文档
├── Dockerfile            # Docker 构建文件
├── .dockerignore         # Docker 构建忽略文件
├── docker-entrypoint.sh  # Docker 容器启动脚本
├── glossary_files/        # 生成的术语表保存目录
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
   - 验证 `.env` 文件中的 AWS_REGION 是否支持 Bedrock 和所需模型

2. **PDF 提取问题**:
   - 确保上传的 PDF 文件可读取且未加密
   - 如果 PDF 是扫描文档，提取效果可能不佳，建议先通过 OCR 工具处理

3. **内容过长错误**:
   - LLM 模型有上下文长度限制，如果 PDF 文件过大，程序会自动截取部分内容
   - 对于大型文档，建议拆分成多个小文件处理

### 日志查看

应用界面提供了实时日志显示区域，您可以在操作过程中查看详细的处理状态和错误信息。这对于诊断问题和了解处理进度非常有帮助。

## 授权

本项目仅供学习和研究使用。使用 AWS Bedrock 服务会产生相应费用，请参考 AWS 官方定价。
