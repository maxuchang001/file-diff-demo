import os
import xml.etree.ElementTree as ET
import text_diff
import diffPdfV2
from ipxact_visualizer import IPXACTVisualizer


def generate_diff_report(file1_path, file2_path):
    """
    生成两个文件的差异报告

    Args:
        file1_path: 第一个文件的路径
        file2_path: 第二个文件的路径

    Returns:
        tuple: (status, result, None)
            - status: 'ok' 表示成功，'no' 表示失败
            - result: 成功时返回HTML格式的差异报告，失败时返回错误信息
    """
    try:
        # 获取文件扩展名
        ext = os.path.splitext(file1_path)[1].lower()

        # 首先判断是否为IPXACT格式的XML文件
        if ext == ".xml" and is_ipxact_file(file1_path) and is_ipxact_file(file2_path):
            visualizer = IPXACTVisualizer(file1_path)
            status, result, _ = visualizer.generate_ipxact_diff_html(
                file1_path, file2_path
            )
            return "ok", result, None

        # 然后判断是否为PDF文件
        elif ext == ".pdf":
            status, result, _ = diffPdfV2.create_diff_report(file1_path, file2_path)
            return status, result, None

        # 最后判断是否为普通文本文件
        elif ext in [
            ".txt",
            ".py",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".java",
            ".js",
            ".html",
            ".css",
            ".json",
            ".md",
            ".csv",
            ".xml",
        ]:
            # 文本文件比较
            status, result, _ = text_diff.generate_text_diff(file1_path, file2_path)
            return status, result, None

        else:
            print(f"不支持的文件类型: {ext}")
            return "no", "不支持的文件类型", None

    except Exception as e:
        print(f"比较过程发生错误: {str(e)}")
        return "no", str(e), None


def is_ipxact_file(file_path):
    """
    检查文件是否为IPXACT格式的XML文件

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否为IPXACT文件
    """
    try:
        ET.register_namespace(
            "spirit", "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2014"
        )
        tree = ET.parse(file_path)
        root = tree.getroot()
        return (
            root.tag
            == "{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2014}component"
        )
    except Exception as e:
        print(f"XML解析错误: {str(e)}")
        return False
