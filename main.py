from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import tempfile
import shutil
from dir_compare import DirectoryComparator
from control import diffControl
from file2html import convert_to_html
import uuid
import hashlib
import filecmp
import json

# 创建静态文件目录
static_dir = os.path.join(os.path.dirname(__file__), 'static')
diffs_dir = os.path.join(static_dir, 'diffs')
separate_dir = os.path.join(static_dir, 'separate')
os.makedirs(diffs_dir, exist_ok=True)
os.makedirs(separate_dir, exist_ok=True)

# 存储临时目录路径的字典
temp_dirs = {}

app = Flask(__name__, 
           static_folder='static',
           static_url_path='/static',
           template_folder='public')

# 配置上传文件夹
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

CORS(app)

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)

@app.route('/api/compare', methods=['POST'])
def compare_directories():
    try:
        # 检查是否是单文件比对
        is_single_file = request.form.get('is_single_file') == 'true'
        
        if is_single_file:
            # 单文件比对逻辑
            file1 = request.files['file1']
            file2 = request.files['file2']
            file1_name = request.form.get('file1_name')
            file2_name = request.form.get('file2_name')
            
            # 创建临时目录
            temp_dir1 = tempfile.mkdtemp()
            temp_dir2 = tempfile.mkdtemp()
            
            # 保存文件
            file1_path = os.path.join(temp_dir1, file1_name)
            file2_path = os.path.join(temp_dir2, file2_name)
            file1.save(file1_path)
            file2.save(file2_path)
            
            # 检查文件是否相同
            identical = filecmp.cmp(file1_path, file2_path, shallow=False)
            
            # 获取文件扩展名
            ext = os.path.splitext(file1_name)[1].lower()
            
            # 生成文件查看报告
            status, html_path = convert_to_html(file1_path)
            if status != 'ok':
                return jsonify({'error': html_path}), 500
            
            # 只在文件不同时生成差异报告
            diff_url = None
            if not identical:
                status, diff_url, _ = diffControl(file1_path, file2_path, file1_name, file2_name, ext)
                if status != 'ok':
                    return jsonify({'error': diff_url}), 500
            
            # 统一返回数据结构
            return jsonify({
                'is_single_file': True,
                'comparison_results': {
                    'only_in_dir1': [],
                    'only_in_dir2': [],
                    'identical': [file1_name] if identical else [],
                    'different': [file1_name] if not identical else []
                },
                'stats': {
                    'only_in_dir1': 0,
                    'only_in_dir2': 0,
                    'identical': 1 if identical else 0,
                    'different': 0 if identical else 1
                },
                'diff_reports': {file1_name: diff_url} if diff_url else {},
                'temp_dirs': {
                    'dir1': temp_dir1,
                    'dir2': temp_dir2
                },
                'dir1_contents': {file1_name: {'html_path': html_path}},
                'dir2_contents': {file2_name: {'html_path': html_path}}
            })
        else:
            # 文件夹比对逻辑
            dir1_files = request.files.getlist('dir1')
            dir2_files = request.files.getlist('dir2')
            
            # 创建临时目录
            temp_dir1 = tempfile.mkdtemp()
            temp_dir2 = tempfile.mkdtemp()
            
            # 保存文件
            for file in dir1_files:
                if file.filename:  # 确保文件名不为空
                    file_path = os.path.join(temp_dir1, file.filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
            
            for file in dir2_files:
                if file.filename:  # 确保文件名不为空
                    file_path = os.path.join(temp_dir2, file.filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
            
            # 比较目录
            comparator = DirectoryComparator(temp_dir1, temp_dir2)
            results = comparator.compare()
            
            # 生成差异报告
            diff_reports = {}
            for file_path in results['different']:
                file1_path = os.path.join(temp_dir1, file_path)
                file2_path = os.path.join(temp_dir2, file_path)
                file1_name = os.path.basename(file_path)
                file2_name = os.path.basename(file_path)
                ext = os.path.splitext(file_path)[1].lower()
                
                status, diff_url, _ = diffControl(file1_path, file2_path, file1_name, file2_name, ext)
                if status == 'ok':
                    diff_reports[file_path] = diff_url
            
            # 计算统计信息
            stats = {
                'only_in_dir1': len(results['only_in_dir1']),
                'only_in_dir2': len(results['only_in_dir2']),
                'identical': len(results['identical']),
                'different': len(results['different'])
            }
            
            return jsonify({
                'is_single_file': False,
                'comparison_results': {
                    'only_in_dir1': results['only_in_dir1'],
                    'only_in_dir2': results['only_in_dir2'],
                    'identical': results['identical'],
                    'different': results['different']
                },
                'stats': stats,
                'diff_reports': diff_reports,
                'temp_dirs': {
                    'dir1': temp_dir1,
                    'dir2': temp_dir2
                },
                'dir1_contents': results['dir1_contents'],
                'dir2_contents': results['dir2_contents']
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/view_file', methods=['GET'])
def view_file():
    try:
        file_path = request.args.get('file')
        dir_type = request.args.get('dir')
        temp_dir = request.args.get('temp_dir')
        diff_reports_str = request.args.get('diff_reports')
        
        if not file_path or not dir_type or not temp_dir:
            return jsonify({'error': 'Missing file path, directory type or temp directory'}), 400
            
        # 使用传入的临时目录路径
        if not os.path.exists(temp_dir):
            return jsonify({'error': 'Directory not found'}), 404
            
        # 构建完整的文件路径
        full_path = os.path.join(temp_dir, file_path)
        if not os.path.exists(full_path):
            return jsonify({'error': 'File not found'}), 404
            
        # 检查是否有预先生成的差异报告
        if diff_reports_str:
            try:
                diff_reports = json.loads(diff_reports_str)
                if file_path in diff_reports:
                    return jsonify({
                        'status': 'ok',
                        'html_url': diff_reports[file_path]
                    })
            except json.JSONDecodeError:
                pass
            
        # 如果没有预先生成的报告，使用 file2html 转换文件
        status, html_path = convert_to_html(full_path)
        if status == 'ok':
            # 返回生成的 HTML 文件的 URL
            return jsonify({
                'status': 'ok',
                'html_url': html_path
            })
        else:
            return jsonify({'error': html_path}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare_file', methods=['POST'])
def compare_file():
    try:
        data = request.get_json()
        file1_path = data.get('file1_path')
        file2_path = data.get('file2_path')
        file1_name = data.get('file1_name')
        file2_name = data.get('file2_name')
        ext = data.get('ext')
        
        if not all([file1_path, file2_path, file1_name, file2_name, ext]):
            return jsonify({'error': 'Missing required parameters'}), 400
            
        # 检查文件是否存在
        if not os.path.exists(file1_path) or not os.path.exists(file2_path):
            return jsonify({'error': 'File not found'}), 404
            
        # 根据文件类型选择不同的处理方式
        if ext == '.txt':
            # 对于文本文件，使用新的比较方式
            status, html_path = convert_to_html(file1_path, file2_path)
            if status != 'ok':
                return jsonify({'error': html_path}), 500
            return jsonify({
                'status': 'ok',
                'diff_url': html_path
            })
        else:
            # 对于其他类型文件，使用原有的比较方式
            status, diff_url, _ = diffControl(file1_path, file2_path, file1_name, file2_name, ext)
            if status != 'ok':
                return jsonify({'error': diff_url}), 500
            return jsonify({
                'status': 'ok',
                'diff_url': diff_url
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 添加清理临时目录的路由
@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    try:
        for dir_type, temp_dir in temp_dirs.items():
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        temp_dirs.clear()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)