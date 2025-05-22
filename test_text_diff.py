import os
import webbrowser
from file2html import convert_to_html

def test_text_diff():
    # 获取当前工作目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建输入文件路径
    file1_path = os.path.join(current_dir, "test_dirs", "dir1", "different.txt")
    file2_path = os.path.join(current_dir, "test_dirs", "dir2", "different.txt")

    print("开始测试文本文件差异比较...")

    # 调用转换函数
    status, html_path = convert_to_html(file1_path, file2_path)

    if status == 'ok':
        # 如果返回的是/static/diffs/xxx.html，转换为本地真实路径
        if html_path.startswith('/static/'):
            html_path = html_path.lstrip('/')
        abs_path = os.path.join(current_dir, html_path)
        print(f"差异报告已生成: {abs_path}")
        # 自动打开生成的HTML文件
        webbrowser.open('file://' + os.path.realpath(abs_path))
    else:
        print(f"❌ 差异报告生成失败：{html_path}")

if __name__ == "__main__":
    test_text_diff() 