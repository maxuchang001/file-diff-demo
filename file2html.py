import os
import base64
import mimetypes
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from io import BytesIO
from markdown import markdown
from docx import Document
import pandas as pd
from pdf2image import convert_from_path
from ipxact_visualizer import IPXACTVisualizer
from text_diff import generate_text_diff

def pdf_to_html(pdf_path):
    dpi=300
    # Step 1: Convert PDF to images
    images = convert_from_path(pdf_path, dpi=dpi)

    # Step 2: Encode images to base64 (直接在内存中处理)
    image_tags = ""
    for idx, img in enumerate(images):
        # 使用 BytesIO 在内存中保存图片
        img_buffer = BytesIO()
        img.save(img_buffer, format="JPEG")
        img_buffer.seek(0)
        
        # 直接从内存中读取并编码
        encoded = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        image_tags += f'<div><img src="data:image/jpeg;base64,{encoded}" style="width:100%; max-width:800px;"/></div>\n'
        
        # 清理内存
        img_buffer.close()
    
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

def file_to_html(file_path, compare_file_path=None):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
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
        # 将文件转换为 HTML
        html_body = file_to_html(input_file, compare_file)

        # 创建 HTML 模板
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
        
        return 'ok', html_template
    except Exception as e:
        print(f"Error in create_diff_report: {str(e)}")
        return 'no', str(e)

# # 示例调用
# if __name__ == "__main__":
#     convert_to_html("file_input/test.pdf")