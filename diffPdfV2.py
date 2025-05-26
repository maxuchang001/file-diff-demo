import base64
import os
import uuid
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import fitz
from io import BytesIO

from summarize import summarize_image  # PyMuPDF

# ===== 配置部分 =====
IMAGE_DIFF_COLOR = 'Orange'
TEXT_DIFF_COLOR = 'Sienna'
LABEL_FONT_SIZE = 36
LABEL_HEIGHT = 50
LABEL_COLOR = "black"
BG_COLOR = "white"
FONT_PATH = "arial.ttf"  # 可替换为系统中可用字体路径

# 配置 Poppler 路径
# POPPLER_PATH = r"C:\mine\program\poppler-24.08.0\Library\bin"

# 配置图片差异显示
DIFF_COLOR = (0, 0, 255)  # 红色
DIFF_THRESHOLD = 30  # 差异阈值

# 配置文本差异显示
TEXT_DIFF_THICKNESS = 2

# ===== 辅助函数 =====

def extract_text_by_page(pdf_path):
    doc = fitz.open(pdf_path)
    return [page.get_text() for page in doc]

def compare_texts(texts1, texts2):
    diff_pages = set()
    for i in range(max(len(texts1), len(texts2))):
        t1 = texts1[i] if i < len(texts1) else ""
        t2 = texts2[i] if i < len(texts2) else ""
        if t1.strip() != t2.strip():
            diff_pages.add(i)
    return diff_pages

def render_pdf_to_images(pdf_path, dpi=200):
    """将PDF渲染为图片"""
    return convert_from_path(pdf_path, dpi=dpi)

def draw_labels(image, label):
    width, height = image.size
    new_img = Image.new('RGB', (width, height + LABEL_HEIGHT), BG_COLOR)
    new_img.paste(image, (0, LABEL_HEIGHT))

    draw = ImageDraw.Draw(new_img)
    try:
        font = ImageFont.truetype(FONT_PATH, LABEL_FONT_SIZE)
    except:
        font = ImageFont.load_default()

    # 兼容 Pillow 10+
    bbox = draw.textbbox((0, 0), label, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) // 2, 10), label, fill=LABEL_COLOR, font=font)

    return new_img


def highlight_differences(img1, img2, mark_text_diff=False):
    img1_np = np.array(img1.convert('RGB'))
    img2_np = np.array(img2.convert('RGB'))

    diff = cv2.absdiff(img1_np, img2_np)
    gray = cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    img1_draw = img1.copy()
    img2_draw = img2.copy()
    draw1 = ImageDraw.Draw(img1_draw)
    draw2 = ImageDraw.Draw(img2_draw)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        draw1.rectangle([x, y, x + w, y + h], outline=IMAGE_DIFF_COLOR, width=2)
        draw2.rectangle([x, y, x + w, y + h], outline=IMAGE_DIFF_COLOR, width=2)

    if mark_text_diff:
        w, h = img1.size
        draw1.rectangle([10, 10, w - 10, h - 10], outline=TEXT_DIFF_COLOR, width=TEXT_DIFF_THICKNESS)
        draw2.rectangle([10, 10, w - 10, h - 10], outline=TEXT_DIFF_COLOR, width=TEXT_DIFF_THICKNESS)

    return img1_draw, img2_draw

def create_combined_image(img_left, img_right, label_left="Old version", label_right="New version"):
    img_left = draw_labels(img_left, label_left)
    img_right = draw_labels(img_right, label_right)
    w, h = img_left.size
    combined = Image.new('RGB', (w * 2, h), BG_COLOR)
    combined.paste(img_left, (0, 0))
    combined.paste(img_right, (w, 0))
    return combined

def generate_html_report(image_data_list, html_output_path):
    html_summarize = ""
    html = ['<html><head><meta charset="UTF-8"><style>body { font-family: sans-serif; text-align: center; }</style></head><body>']
    html.append("<h1>PDF Variance comparison report</h1>")
    
    for i, img_data in enumerate(image_data_list):
        html.append(f"<h2>Page {i + 1}</h2>")
        
        # 直接使用内存中的图片数据
        encoded = base64.b64encode(img_data).decode('utf-8')
        html.append(f'<img src="data:image/jpeg;base64,{encoded}" style="width:100%; border:1px solid #ccc;"/><hr>')
        # 添加智能总结
        image_result = summarize_image(encoded)
        html.append(image_result)
        html_summarize += image_result

    html.append("</body></html>")

    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    return html_summarize

# ===== 主程序 =====

def diff_pdfs_side_by_side(pdf1_path, pdf2_path, file1_name, file2_name, output_dir):
    print("📄 提取文本差异...")
    texts1 = extract_text_by_page(pdf1_path)
    texts2 = extract_text_by_page(pdf2_path)
    text_diff_pages = compare_texts(texts1, texts2)

    print("🖼️ 渲染 PDF 页面为图像...")
    images1 = render_pdf_to_images(pdf1_path)
    images2 = render_pdf_to_images(pdf2_path)

    combined_image_data_list = []

    for i in range(max(len(images1), len(images2))):
        img1 = images1[i] if i < len(images1) else Image.new('RGB', images2[0].size, color='white')
        img2 = images2[i] if i < len(images2) else Image.new('RGB', images1[0].size, color='white')

        mark_text = i in text_diff_pages
        img1_marked, img2_marked = highlight_differences(img1, img2, mark_text_diff=mark_text)
        combined = create_combined_image(img1_marked, img2_marked, file1_name, file2_name)

        # 将图片数据保存到内存中
        img_byte_arr = BytesIO()
        combined.save(img_byte_arr, format='PNG')
        combined_image_data_list.append(img_byte_arr.getvalue())
        print(f"✅ 页面 {i+1} 完成")

    html_path = os.path.join(output_dir, "diff_report.html")
    html_summarize = generate_html_report(combined_image_data_list, html_path)
    html_summarize = ""
    print(f"📄 HTML 报告生成完成: {html_path}")
    return html_path, html_summarize

def create_diff_report(pdf1, pdf2):
    """
    创建PDF文件的差异报告
    
    Args:
        pdf1: 第一个PDF文件的路径
        pdf2: 第二个PDF文件的路径
        
    Returns:
        tuple: (status, result, summary)
            - status: 'ok' 表示成功，'no' 表示失败
            - result: 成功时返回HTML内容，失败时返回错误信息
            - summary: 差异摘要
    """
    try:
        # 获取文件名
        file1_name = os.path.basename(pdf1)
        file2_name = os.path.basename(pdf2)
        
        # 使用 static/diffs 目录
        static_dir = os.path.join(os.path.dirname(__file__), 'static', 'diffs')
        os.makedirs(static_dir, exist_ok=True)
        
        # 创建唯一的输出目录
        output_dir = os.path.join(static_dir, uuid.uuid4().hex)
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成差异报告
        html_path, html_summarize = diff_pdfs_side_by_side(pdf1, pdf2, file1_name, file2_name, output_dir)
        
        # 读取生成的HTML内容
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        return 'ok', html_content, html_summarize
    except Exception as e:
        print(f"Error in create_diff_report: {str(e)}")
        return 'no', str(e), ""