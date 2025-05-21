import os
import shutil
import tempfile
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import xml.etree.ElementTree as ET
from dir_compare import DirectoryComparator
import text_diff
import diffPdfV2
from datetime import datetime
from ipxact_visualizer import IPXACTVisualizer

def diffControl(file1, file2, file1_name, file2_name, ext):
    try:
        # 获取文件扩展名
        ext = ext.lower()
        
        # 根据文件类型选择比较方法
        if ext in ['.txt', '.py', '.c', '.cpp', '.h', '.hpp', '.java', '.js', '.html', '.css', '.json', '.md', '.csv']:
            # 文本文件比较
            status, result = text_diff.generate_text_diff(file1, file2, file1_name, file2_name)
            return status, result, None
        elif ext == '.pdf':
            # PDF文件比较
            return diffPdfV2.create_diff_report(file1, file2, file1_name, file2_name)
        elif ext == '.xml':
            # XML文件需要特殊处理
            return diffFile(file1, file2, file1_name, file2_name, ext)
        else:
            return 'no', '不支持的文件类型', None
    except Exception as e:
        print(f"Error in diffControl: {str(e)}")
        return 'no', str(e), None

def is_ipxact_file(file_path):
    try:
        # 注册命名空间
        ET.register_namespace('spirit', 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2014')
        
        # 解析XML文件
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # 检查根元素
        if root.tag != '{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2014}component':
            return False
            
        return True
    except Exception as e:
        print(f"XML parsing error: {str(e)}")
        return False

def diffFile(file1_path, file2_path, file1_name, file2_name, ext):
    # 支持的文本文件扩展名
    text_extensions = ['.txt', '.py', '.c', '.cpp', '.h', '.hpp', '.java', '.js', '.html', '.css', '.json', '.md', '.csv']
    
    if ext.lower() == '.pdf':
        # 调用 diffPdfV2 模块进行比较
        return diffPdfV2.create_diff_report(file1_path, file2_path, file1_name, file2_name)
    elif ext.lower() == '.xml':
        print(f"处理XML文件: {file1_path} 和 {file2_path}")
        # 检查是否为IPXACT文件
        is_ipxact1 = is_ipxact_file(file1_path)
        is_ipxact2 = is_ipxact_file(file2_path)
        print(f"文件1是IPXACT: {is_ipxact1}")
        print(f"文件2是IPXACT: {is_ipxact2}")
        
        if is_ipxact1 and is_ipxact2:
            try:
                # 使用ipxact_visualizer中的函数进行比较
                visualizer = IPXACTVisualizer(file1_path)
                # 生成唯一的输出文件名
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'diff_{file1_name}_vs_{file2_name}_{timestamp}.html'
                output_path = os.path.join(os.path.dirname(__file__), 'static', 'diffs', output_file)
                success = visualizer.generate_ipxact_diff_html(file1_path, file2_path, output_path)
                if success:
                    return 'ok', f'/static/diffs/{output_file}', None
                else:
                    return 'no', '生成IPXACT比较报告失败', None
            except Exception as e:
                print(f"IPXACT比较错误: {str(e)}")
                return 'no', str(e), None
        else:
            # 普通XML文件,使用文本比较
            status, result = text_diff.generate_text_diff(file1_path, file2_path, file1_name, file2_name)
            return status, result, None
    elif ext.lower() in text_extensions:
        # 调用文本差异对比模块
        status, result = text_diff.generate_text_diff(file1_path, file2_path, file1_name, file2_name)
        return status, result, None
    elif ext.lower() == '.docx':
        # docx 文件需先转换为 pdf
        return 'no', 'docx 不支持的文件类型', None
    elif ext.lower() == '.xlsx':
        # xlsx 文件需先转换为 pdf
        return 'no', 'xlsx 不支持的文件类型', None
    elif ext.lower() == '.pptx':
        # pptx 文件需先转换为 pdf
        return 'no', 'pptx 不支持的文件类型', None
    else:
        # 其他文件类型不支持
        return 'no', '不支持的文件类型', None