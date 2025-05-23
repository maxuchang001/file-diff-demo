import difflib
import os
import tempfile
import shutil
import webbrowser
from file2html import convert_to_html

def generate_text_diff(file1_path, file2_path, file1_name, file2_name):
    """
    生成两个文本文件之间的差异对比 HTML
    
    Args:
        file1_path: 第一个文件的路径
        file2_path: 第二个文件的路径
        file1_name: 第一个文件的显示名称
        file2_name: 第二个文件的显示名称
        
    Returns:
        tuple: (状态, 结果)
            - 状态: 'ok' 表示成功，'no' 表示失败
            - 结果: 成功时返回 HTML 文件路径，失败时返回错误信息
    """
    try:
        print(f"开始处理文本文件差异对比:")
        print(f"文件1: {file1_path}")
        print(f"文件2: {file2_path}")
        
        # 读取文件内容
        with open(file1_path, 'r', encoding='utf-8') as f1:
            old_lines = f1.read().splitlines()
        with open(file2_path, 'r', encoding='utf-8') as f2:
            new_lines = f2.read().splitlines()
            
        print(f"文件1行数: {len(old_lines)}")
        print(f"文件2行数: {len(new_lines)}")
            
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, 'diff.html')
        
        # 生成差异对比 HTML
        html = difflib.HtmlDiff(tabsize=4, wrapcolumn=80) \
            .make_file(old_lines, new_lines,
                      fromdesc=file1_name, todesc=file2_name,
                      context=True, numlines=3)
        
        # 添加自定义样式
        html = html.replace('</head>', '''
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }
            table.diff {
                border-collapse: collapse;
                width: 100%;
                background-color: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            }
            .diff_header {
                background-color: #e0e0e0;
                padding: 8px;
                font-weight: bold;
            }
            td.diff_header {
                text-align: right;
                padding: 8px;
            }
            .diff_next {
                background-color: #f0f0f0;
            }
            .diff_add {
                background-color: #e6ffe6;
            }
            .diff_chg {
                background-color: #ffffcc;
            }
            .diff_sub {
                background-color: #ffe6e6;
            }
            td {
                padding: 4px 8px;
                font-family: monospace;
                white-space: pre;
            }
        </style>
        </head>
        ''')
        
        # 保存 HTML 文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
            
        print(f"差异对比 HTML 已生成: {output_path}")
        
        # 将文件复制到静态文件目录
        static_dir = os.path.join(os.path.dirname(__file__), 'static', 'diffs')
        os.makedirs(static_dir, exist_ok=True)
        static_path = os.path.join(static_dir, f'diff_{os.path.basename(temp_dir)}.html')
        shutil.copy2(output_path, static_path)
        
        # 返回静态文件路径
        return 'ok', f'/static/diffs/diff_{os.path.basename(temp_dir)}.html'
        
    except Exception as e:
        print(f"生成差异对比时出错: {str(e)}")
        return 'no', str(e) 

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