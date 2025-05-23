import os
import webbrowser
from ipxact_visualizer import IPXACTVisualizer

def test_ipxact_diff():
    # 获取当前工作目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建输入文件路径
    xml1_path = os.path.join(current_dir, "test_dirs", "dir1", "ipxact.xml")
    xml2_path = os.path.join(current_dir, "test_dirs", "dir2", "ipxact.xml")
    
    # 构建输出文件路径
    output_path = os.path.join(current_dir, "ipxact_diff_report.html")
    
    # 创建IPXACTVisualizer实例
    visualizer = IPXACTVisualizer(xml1_path)
    
    # 生成差异报告
    success = visualizer.generate_ipxact_diff_html(xml1_path, xml2_path, output_path)
    
    if success:
        # 自动打开生成的HTML文件
        webbrowser.open('file://' + os.path.realpath(output_path))
    else:
        print("生成差异报告失败")

if __name__ == "__main__":
    test_ipxact_diff() 