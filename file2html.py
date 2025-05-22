import os
import base64
import mimetypes
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
import difflib

from markdown import markdown
from docx import Document
import pandas as pd
from pdf2image import convert_from_path
from ipxact_visualizer import IPXACTVisualizer
from summarize import summarize_image, client, model


def pdf_to_html(pdf_path):
    dpi=300
    # Step 1: Convert PDF to images
    images = convert_from_path(pdf_path, dpi=dpi)

    # Step 2: Encode images to base64
    image_tags = ""
    for idx, img in enumerate(images):
        with open(f"page_{idx+1}.jpg", "wb") as f:
            img.save(f, "JPEG")

        with open(f"page_{idx+1}.jpg", "rb") as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            image_tags += f'<div><img src="data:image/jpeg;base64,{encoded}" style="width:100%; max-width:800px;"/></div>\n'

        os.remove(f"page_{idx+1}.jpg")  # 可选：删除临时图像文件
    return image_tags

def is_ipxact_file(file_path):
    """检查文件是否为 IPXACT 文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        tuple: (bool, str)
            bool: 是否为 IPXACT 文件
            str: 如果不是 IPXACT 文件，返回原因
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # 检查命名空间
        ns = {
            'spirit': 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2014'
        }
        
        # 检查根元素
        if not root.tag.endswith('component'):
            return False, "根元素不是 component"
            
        # 检查命名空间
        if not root.tag.startswith('{http://www.spiritconsortium.org/XMLSchema/SPIRIT/'):
            return False, "不是有效的 IPXACT 命名空间"
            
        # 检查必需的元素
        required_elements = ['name', 'version', 'vendor']
        for elem in required_elements:
            if root.find(f'spirit:{elem}', ns) is None:
                return False, f"缺少必需元素: {elem}"
                
        return True, "有效的 IPXACT 文件"
        
    except ET.ParseError as e:
        return False, f"XML 解析错误: {str(e)}"
    except FileNotFoundError:
        return False, "文件不存在"
    except Exception as e:
        return False, f"未知错误: {str(e)}"

def get_text_diff_summary(text1, text2):
    """使用AI生成文本差异的总结"""
    # 生成差异文本
    diff = difflib.unified_diff(
        text1.splitlines(),
        text2.splitlines(),
        lineterm='',
        n=3  # 显示上下文行数
    )
    diff_text = '\n'.join(diff)
    
    # 构建提示词
    prompt = f"""Please analyze the following text differences and provide a concise summary in English. 
    Focus on the key changes and their impact. Format the output as a clean, left-aligned HTML div.
    
    Text differences:
    {diff_text}
    """
    
    # 调用AI生成总结
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content

def file_to_html(file_path, compare_file_path=None):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if compare_file_path:
            with open(compare_file_path, 'r', encoding='utf-8') as f:
                compare_content = f.read()
            
            # 使用原有的文档对比功能
            from text_diff import generate_text_diff
            status, diff_html = generate_text_diff(file_path, compare_file_path, 
                                                 os.path.basename(file_path), 
                                                 os.path.basename(compare_file_path))
            
            if status == 'ok':
                # 读取diff_html文件内容
                diff_html_path = os.path.join(os.path.dirname(__file__), diff_html.lstrip('/').replace('/', os.sep))
                with open(diff_html_path, 'r', encoding='utf-8') as f:
                    diff_html_content = f.read()
                # 添加智能总结
                summary = get_text_diff_summary(content, compare_content)
                
                return f"""
                {diff_html_content}
                <div class="summary-section">
                    <h3>AI Summary of Changes</h3>
                    {summary}
                </div>
                """
            else:
                return f"<p>⚠️ 文档对比失败: {diff_html}</p>"
        else:
            return f"<pre>{content}</pre>"

    elif ext == '.md':
        with open(file_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
        return markdown(md_text)

    elif ext == '.docx':
        doc = Document(file_path)
        html = ""
        for para in doc.paragraphs:
            html += f"<p>{para.text}</p>\n"
        return html

    elif ext == '.pdf':
        return pdf_to_html(file_path)

    elif ext in ['.xls', '.xlsx']:
        df = pd.read_excel(file_path)
        return df.to_html(index=False)

    elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
        with open(file_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        mime = mimetypes.guess_type(file_path)[0]
        return f'<img src="data:{mime};base64,{encoded}" alt="image" />'

    elif ext == '.xml':
        is_ipxact, reason = is_ipxact_file(file_path)
        if is_ipxact:
            # 处理 IPXACT 文件
            visualizer = IPXACTVisualizer(file_path)
            status, result = visualizer.generate_single_file_html(file_path, file_path + '.html')
            if status == 'ok':
                with open(result, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return f"<p>⚠️ IPXACT 文件处理失败: {result}</p>"
        else:
            # 处理普通 XML 文件
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                xml_str = ET.tostring(root, encoding='unicode')
                return f"<pre>{xml_str}</pre>"
            except Exception as e:
                return f"<p>⚠️ XML 文件处理失败: {str(e)}</p>"

    else:
        return f"<p>⚠️ 不支持的文件类型: {ext}</p>"

def convert_to_html(input_file, compare_file=None):
    try:
        # 使用 static/diffs 目录
        static_dir = os.path.join(os.path.dirname(__file__), 'static', 'diffs')
        os.makedirs(static_dir, exist_ok=True)
        
        # 创建唯一的输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'view_{os.path.basename(input_file)}_{timestamp}.html'
        output_path = os.path.join(static_dir, output_file)

        html_body = file_to_html(input_file, compare_file)

        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>{os.path.basename(input_file)}</title>
            <style>
                body {{ font-family: sans-serif; padding: 20px; text-align: center;}}
                img {{ box-shadow: 0 0 10px rgba(0,0,0,0.2); margin-bottom: 30px; }}
                .file-list {{ list-style: none; padding: 0; }}
                .file-list li {{ 
                    margin: 10px 0; 
                    padding: 10px; 
                    background-color: #f5f5f5; 
                    border-radius: 5px;
                    cursor: pointer;
                    transition: background-color 0.3s;
                }}
                .file-list li:hover {{ 
                    background-color: #e0e0e0;
                }}
                .file-list li a {{
                    text-decoration: none;
                    color: #333;
                    display: block;
                    width: 100%;
                    height: 100%;
                }}
                .summary-section {{
                    text-align: left;
                    margin: 20px 0;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    border-left: 4px solid #007bff;
                }}
                .content-section {{
                    text-align: left;
                    margin: 20px 0;
                }}
                .content-section pre {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
            </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        print(f"✅ HTML 文件已生成: {output_path}")
        
        # 返回相对于 static 目录的路径
        return 'ok', f'/static/diffs/{output_file}'
    except Exception as e:
        print(f"Error in create_diff_report: {str(e)}")
        return 'no', str(e)

# # 示例调用
# if __name__ == "__main__":
#     convert_to_html("file_input/test.pdf")