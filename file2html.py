import os
import base64
import mimetypes
import uuid

from markdown import markdown
from docx import Document
import pandas as pd
from pdf2image import convert_from_path


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

def file_to_html(file_path):
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

    else:
        return f"<p>⚠️ 不支持的文件类型: {ext}</p>"

def convert_to_html(input_file):
    try:
        # 使用 static/diffs 目录
        static_dir = os.path.join(os.path.dirname(__file__), 'static', 'separate')
        os.makedirs(static_dir, exist_ok=True)
        
        # 创建唯一的输出目录
        output_dir = os.path.join(static_dir, uuid.uuid4().hex)
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "outputfile.html")

        html_body = file_to_html(input_file)

        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>{os.path.basename(input_file)}</title>
            <style>
                body {{ font-family: sans-serif; padding: 20px; text-align: center;}}
                img {{ box-shadow: 0 0 10px rgba(0,0,0,0.2); margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_template)
        print(f"✅ HTML 文件已生成: {output_file}")
        
        # 返回相对于 static 目录的路径
        return 'ok', output_file
    except Exception as e:
        print(f"Error in create_diff_report: {str(e)}")
        return 'no', str(e)

# # 示例调用
# if __name__ == "__main__":
#     convert_to_html("file_input/test.pdf")