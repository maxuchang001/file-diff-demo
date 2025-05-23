import difflib
import os
import webbrowser
from summarize import client, model

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

def generate_text_diff(file1_path, file2_path, file1_name, file2_name, include_ai_summary=True):
    """
    生成两个文本文件之间的差异对比 HTML
    
    Args:
        file1_path: 第一个文件的路径
        file2_path: 第二个文件的路径
        file1_name: 第一个文件的显示名称
        file2_name: 第二个文件的显示名称
        include_ai_summary: 是否包含 AI 总结
        
    Returns:
        tuple: (状态, 结果)
            - 状态: 'ok' 表示成功，'no' 表示失败
            - 结果: 成功时返回 HTML 内容，失败时返回错误信息
    """
    try:
        print(f"开始处理文本文件差异对比:")
        print(f"文件1: {file1_path}")
        print(f"文件2: {file2_path}")
        
        # 读取文件内容
        with open(file1_path, 'r', encoding='utf-8') as f1:
            old_lines = f1.read().splitlines()
            old_text = '\n'.join(old_lines)
        with open(file2_path, 'r', encoding='utf-8') as f2:
            new_lines = f2.read().splitlines()
            new_text = '\n'.join(new_lines)
            
        print(f"文件1行数: {len(old_lines)}")
        print(f"文件2行数: {len(new_lines)}")
        
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
            .summary-section {
                text-align: left;
                margin: 20px 0;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }
        </style>
        </head>
        ''')
        
        # 如果需要 AI 总结，添加总结部分
        if include_ai_summary:
            summary = get_text_diff_summary(old_text, new_text)
            html = html.replace('</body>', f'''
            <div class="summary-section">
                <h3>AI Summary of Changes</h3>
                {summary}
            </div>
            </body>
            ''')
        
        return 'ok', html
        
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
    status, html_content = generate_text_diff(file1_path, file2_path, 
                                            os.path.basename(file1_path),
                                            os.path.basename(file2_path))

    if status == 'ok':
        # 保存 HTML 内容到文件
        output_path = os.path.join(current_dir, "test_diff.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ 差异报告已保存到：{output_path}")
        
        # 自动打开生成的HTML文件
        webbrowser.open('file://' + os.path.realpath(output_path))
    else:
        print(f"❌ 差异报告生成失败：{html_content}")

if __name__ == "__main__":
    test_text_diff() 