#!/usr/bin/env python3
"""
Gradio Web Interface for PDF Term Extractor

This script provides an interactive web interface for extracting professional 
terminology pairs from Chinese-English PDF documents using AWS Bedrock Converse API.
"""
import os
import tempfile
import logging
import pandas as pd
import gradio as gr
from pathlib import Path
from dotenv import load_dotenv

from src.pdf_processor import PDFProcessor
from src.bedrock_client import BedrockClient
from src.term_extractor import TermExtractor

# Configure logging with a custom formatter for the web interface
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Stream handler to capture logs for display in the UI
class LogCaptureHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        self.logs = []
        
    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append(log_entry)
        
    def get_logs(self):
        return "\n".join(self.logs)
        
    def clear_logs(self):
        self.logs = []

# Create a custom log handler
log_handler = LogCaptureHandler()
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S"))
logger.addHandler(log_handler)
logging.getLogger("src.pdf_processor").addHandler(log_handler)
logging.getLogger("src.bedrock_client").addHandler(log_handler)
logging.getLogger("src.term_extractor").addHandler(log_handler)

# Load environment variables
load_dotenv()

# Check AWS credentials
required_env_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]

# Available models list
MODELS = [
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0",  # Default
    "us.amazon.nova-lite-v1:0",
    "us.amazon.nova-pro-v1:0"
]

# Default system prompt for terminology extraction
DEFAULT_PROMPT = """As a professional translator and terminologist, please help extract professional terminology pairs from these parallel Chinese and English texts:

CHINESE TEXT:
{chinese_text}

ENGLISH TEXT:
{english_text}

Identify all specific professional terms and specialized vocabulary that appears in both texts.
Return the results as an XML-formatted list of term entries with these fields:
- "name": a 6-character random string (e.g., "A2B3C4", "X7Y8Z9", etc.)
- "ZH_CN": The Chinese term
- "EN_US": The corresponding English term

IMPORTANT GUIDELINES:
1. Focus on specialized terminology specific to this document's domain
2. Include only terms that appear in both texts
3. Extract ONLY professional/technical terms, not common words
4. Ensure accurate pairing between Chinese and English terms
5. Return ONLY the XML data without any other text

Return format example:
<terminology>
  <term>
    <name>A2B3C4</name>
    <ZH_CN>数据库</ZH_CN>
    <EN_US>database</EN_US>
  </term>
  <term>
    <name>X7Y8Z9</name>
    <ZH_CN>云计算</ZH_CN>
    <EN_US>cloud computing</EN_US>
  </term>
</terminology>"""

def check_environment():
    """Check if the required environment variables are set."""
    if missing_vars:
        return False, f"Missing AWS credentials: {', '.join(missing_vars)}. Please set these in your .env file."
    return True, "AWS credentials are properly configured."

def extract_terms(chinese_pdf, english_pdf, model_id, custom_prompt, progress=gr.Progress()):
    """
    Process PDF files and extract terminology pairs.
    
    Args:
        chinese_pdf (tempfile): Uploaded Chinese PDF file
        english_pdf (tempfile): Uploaded English PDF file
        model_id (str): AWS Bedrock model ID
        custom_prompt (str): Custom prompt for terminology extraction
        progress (gr.Progress): Gradio progress bar
        
    Returns:
        tuple: (DataFrame of results, CSV file path, log messages)
    """
    log_handler.clear_logs()
    
    if chinese_pdf is None or english_pdf is None:
        logger.error("Both Chinese and English PDF files must be uploaded.")
        return None, None, log_handler.get_logs()
    
    try:
        # Initialize components
        logger.info("Initializing PDF processor")
        pdf_processor = PDFProcessor()
        
        logger.info(f"Initializing Bedrock client with model: {model_id}")
        progress(0.1, "Initializing components...")
        bedrock_client = BedrockClient(model_id=model_id)
        
        # Set custom prompt if provided
        if custom_prompt and custom_prompt.strip() != "":
            # This will need to be implemented in term_extractor.py
            logger.info("Using custom prompt for terminology extraction")
            term_extractor = TermExtractor(bedrock_client, custom_prompt=custom_prompt)
        else:
            term_extractor = TermExtractor(bedrock_client)
            
        # Process Chinese PDF
        logger.info(f"Processing Chinese PDF: {os.path.basename(chinese_pdf.name)}")
        progress(0.2, "Processing Chinese PDF...")
        chinese_text = pdf_processor.extract_text(chinese_pdf.name)
        logger.info(f"Extracted {len(chinese_text)} characters from Chinese PDF")
        
        # Process English PDF
        logger.info(f"Processing English PDF: {os.path.basename(english_pdf.name)}")
        progress(0.4, "Processing English PDF...")
        english_text = pdf_processor.extract_text(english_pdf.name)
        logger.info(f"Extracted {len(english_text)} characters from English PDF")
        
        # Extract terminology pairs
        logger.info("Extracting terminology pairs (this may take a while)...")
        progress(0.6, "Extracting terminology pairs...")
        terminology_pairs = term_extractor.extract_terms(chinese_text, english_text)
        
        # Create results dataframe for display
        logger.info(f"Found {len(terminology_pairs)} terminology pairs")
        progress(0.9, "Processing results...")
        
        if terminology_pairs:
            df = pd.DataFrame(terminology_pairs)
            
            # Create glossary_files directory if it doesn't exist
            os.makedirs("glossary_files", exist_ok=True)
            
            # Generate a timestamped filename for the CSV
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"glossary_files/terminology_{timestamp}.csv"
            
            # Save the CSV file to the glossary_files directory
            term_extractor.save_to_csv(terminology_pairs, csv_filename)
            logger.info(f"Results saved to file: {csv_filename}")
            
            progress(1.0, "Complete!")
            return df, csv_filename, log_handler.get_logs()
        else:
            logger.warning("No terminology pairs found")
            return None, None, log_handler.get_logs()
            
    except Exception as e:
        logger.error(f"Error extracting terminology: {str(e)}")
        return None, None, log_handler.get_logs()

def create_app():
    """Create and configure the Gradio app."""
    
    # Check environment variables
    env_ok, env_message = check_environment()
    
    # Custom CSS for better styling
    css = """
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
        color: #856404;
    }
    .title-section {
        margin-bottom: 20px;
    }
    .result-section {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 10px;
        margin-top: 10px;
    }
    /* 优化PDF上传区域的样式 */
    .gradio-file {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 0 8px;
        background-color: #f9f9f9;
        min-height: 120px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .gradio-file:hover {
        box-shadow: 0 5px 10px rgba(0,0,0,0.12);
        transform: translateY(-2px);
    }
    .gradio-file::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        z-index: 1;
    }
    /* 英文PDF区域标识色 */
    .gradio-file:first-child::before {
        background: linear-gradient(to right, #fbbc05, #ea4335);
    }
    /* 中文PDF区域标识色 */
    .gradio-file:last-child::before {
        background: linear-gradient(to right, #4285f4, #34a853);
    }
    /* 美化文件上传控件 */
    .file-preview {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    /* 优化行间距和PDF上传区域整体布局 */
    .pdf-upload-row {
        margin-bottom: 25px !important;
        gap: 20px;
        display: flex;
        justify-content: space-between;
    }
    
    /* Make file labels more prominent */
    .gradio-file label {
        font-weight: 600;
        color: #333;
        margin-bottom: 8px;
    }
    
    /* Better file upload button styling */
    .gradio-file button {
        background-color: #f2f2f2;
        border: 1px dashed #ccc;
        transition: all 0.2s ease;
    }
    
    .gradio-file button:hover {
        background-color: #e6e6e6;
        border-color: #999;
    }
    
    /* 确保两个文件上传组件的宽度相等 */
    .gradio-file {
        flex: 1;
        min-width: 0; /* 防止flex子项溢出 */
    }
    """
    
    with gr.Blocks(title="PDF Term Extractor", css=css) as app:
        with gr.Row(elem_classes=["title-section"]):
            with gr.Column():
                gr.Markdown("# PDF 专业术语提取器")
                gr.Markdown("从中英文对照的 PDF 文件中提取专业术语，并保存为 CSV 文件。")
        
        if not env_ok:
            with gr.Row():
                with gr.Column():
                    gr.Markdown(f"""⚠️ **环境配置错误**
                    
                    {env_message}
                    
                    请在 `.env` 文件中配置正确的 AWS 凭证信息，然后重启应用。
                    """, elem_classes=["warning-box"])
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## 1. 上传 PDF 文件")
                # 左右分栏式布局设计，将中英文PDF上传区域分别放置在同一行的两个scale
                with gr.Column(scale=2):
                    with gr.Row(elem_classes=["pdf-upload-row"]):
                        english_pdf = gr.File(
                            label="English Document (英文文档)", 
                            file_types=[".pdf"], 
                            type="filepath"
                        )
                        chinese_pdf = gr.File(
                            label="Chinese Document (中文文档)", 
                            file_types=[".pdf"], 
                            type="filepath"
                        )
                
                gr.Markdown("## 2. 选择模型")
                model_dropdown = gr.Dropdown(
                    choices=MODELS, 
                    value=MODELS[0], 
                    label="AWS Bedrock 模型"
                )
                
                gr.Markdown("## 3. 自定义提示词（可选）")
                custom_prompt = gr.TextArea(
                    value=DEFAULT_PROMPT, 
                    label="提示词模板", 
                    lines=8,
                    placeholder="自定义用于术语提取的提示词"
                )
                
                extract_button = gr.Button("提取专业术语", variant="primary")
                
            with gr.Column(scale=1, elem_classes=["result-section"]):
                gr.Markdown("## 术语提取结果")
                with gr.Row():
                    output_table = gr.DataFrame(
                        headers=["name", "ZH_CN", "EN_US"], 
                        label="提取的术语", 
                        interactive=False
                    )
                
                with gr.Row():
                    download_button = gr.Button("下载术语表 CSV", variant="secondary", visible=False)
                    clear_button = gr.Button("清空结果", variant="stop", visible=False)
                
                # Hidden component to store the CSV path
                csv_path = gr.State(value=None)
                
                # Actual file download component
                download_csv = gr.File(label="Download Term List", interactive=False)
                
                gr.Markdown("## 处理日志")
                log_output = gr.TextArea(label="处理日志", interactive=False, lines=10)
        
        # Set up event handlers
        extract_button.click(
            fn=extract_terms,
            inputs=[chinese_pdf, english_pdf, model_dropdown, custom_prompt],
            outputs=[output_table, csv_path, log_output],
            show_progress=True
        ).then(
            fn=lambda x: (gr.update(visible=x is not None), gr.update(visible=x is not None)),
            inputs=[csv_path],
            outputs=[download_button, clear_button]
        )
        
        # Enhanced file download implementation
        def setup_download(file_path):
            """Prepare the CSV file for download"""
            if file_path and os.path.exists(file_path):
                logger.info(f"Preparing to download file: {file_path}")
                return gr.update(value=file_path, visible=True)
            return gr.update(value=None, visible=False)
            
        download_button.click(
            fn=setup_download,
            inputs=[csv_path],
            outputs=[download_csv]
        )
        
        # Clear results function
        def clear_results():
            log_handler.clear_logs()
            return None, None, "", None, gr.update(visible=False), gr.update(visible=False)
        
        # Connect clear button
        clear_button.click(
            fn=clear_results,
            inputs=[],
            outputs=[output_table, csv_path, log_output, download_csv, download_button, clear_button]
        )
        
        # Clear log when files change
        chinese_pdf.change(lambda: "", None, log_output)
        english_pdf.change(lambda: "", None, log_output)
        
    return app

if __name__ == "__main__":
    # Create and launch the app
    demo = create_app()
    demo.launch(share=True, inbrowser=True)
