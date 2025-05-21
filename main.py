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
            # 处理单文件比对
            file1 = request.files['file1']
            file2 = request.files['file2']
            file1_name = request.form.get('file1_name')
            file2_name = request.form.get('file2_name')
            
            # 创建两个临时目录
            temp_dir1 = tempfile.mkdtemp(prefix='file_diff_dir1_')
            temp_dir2 = tempfile.mkdtemp(prefix='file_diff_dir2_')
            
            try:
                # 保存文件
                file1_path = os.path.join(temp_dir1, file1_name)
                file2_path = os.path.join(temp_dir2, file2_name)
                file1.save(file1_path)
                file2.save(file2_path)
                
                # 计算文件哈希值
                def calculate_file_hash(file_path):
                    sha256_hash = hashlib.sha256()
                    with open(file_path, "rb") as f:
                        for byte_block in iter(lambda: f.read(4096), b""):
                            sha256_hash.update(byte_block)
                    return sha256_hash.hexdigest()
                
                file1_hash = calculate_file_hash(file1_path)
                file2_hash = calculate_file_hash(file2_path)
                
                # 判断文件是否相同
                identical = file1_hash == file2_hash
                
                # 保存临时目录路径
                temp_dirs['dir1'] = temp_dir1
                temp_dirs['dir2'] = temp_dir2
                
                return jsonify({
                    'is_single_file': True,
                    'identical': identical,
                    'temp_dirs': {
                        'dir1': temp_dir1,
                        'dir2': temp_dir2
                    },
                    'comparison_results': {
                        'only_in_dir1': [],
                        'only_in_dir2': [],
                        'different': [file1_name] if not identical else [],
                        'identical': [file1_name] if identical else []
                    }
                })
            except Exception as e:
                # 如果发生错误，清理临时目录
                shutil.rmtree(temp_dir1, ignore_errors=True)
                shutil.rmtree(temp_dir2, ignore_errors=True)
                raise e
        
        # 原有的文件夹比对逻辑
        dir1_files = request.files.getlist('dir1')
        dir2_files = request.files.getlist('dir2')
        
        # 创建两个临时目录
        temp_dir1 = tempfile.mkdtemp(prefix='file_diff_dir1_')
        temp_dir2 = tempfile.mkdtemp(prefix='file_diff_dir2_')
        
        # 保存临时目录路径
        temp_dirs['dir1'] = temp_dir1
        temp_dirs['dir2'] = temp_dir2
        
        try:
            # 保存dir1文件
            for file in dir1_files:
                rel_path = file.filename
                save_path = os.path.join(temp_dir1, rel_path)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                file.save(save_path)
            # 保存dir2文件
            for file in dir2_files:
                rel_path = file.filename
                save_path = os.path.join(temp_dir2, rel_path)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                file.save(save_path)
            # 比较目录
            comparator = DirectoryComparator(temp_dir1, temp_dir2)
            result = comparator.compare()
            
            # 将临时目录路径添加到结果中
            result['temp_dirs'] = {
                'dir1': temp_dir1,
                'dir2': temp_dir2
            }
            
            return jsonify(result)
        except Exception as e:
            # 如果发生错误，清理临时目录
            shutil.rmtree(temp_dir1, ignore_errors=True)
            shutil.rmtree(temp_dir2, ignore_errors=True)
            if 'dir1' in temp_dirs:
                del temp_dirs['dir1']
            if 'dir2' in temp_dirs:
                del temp_dirs['dir2']
            raise e
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/view_file', methods=['GET'])
def view_file():
    try:
        file_path = request.args.get('file')
        dir_type = request.args.get('dir')
        temp_dir = request.args.get('temp_dir')
        
        if not file_path or not dir_type or not temp_dir:
            return jsonify({'error': 'Missing file path, directory type or temp directory'}), 400
            
        # 使用传入的临时目录路径
        if not os.path.exists(temp_dir):
            return jsonify({'error': 'Directory not found'}), 404
            
        # 构建完整的文件路径
        full_path = os.path.join(temp_dir, file_path)
        if not os.path.exists(full_path):
            return jsonify({'error': 'File not found'}), 404
            
        # 使用 file2html 转换文件
        status, html_path = convert_to_html(full_path)
        if status == 'ok':
            # 直接返回生成的 HTML 文件
            return send_from_directory(os.path.dirname(html_path), os.path.basename(html_path))
        else:
            return jsonify({'error': html_path}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare_file', methods=['POST'])
def compare_file():
    try:
        # 创建两个独立的临时目录
        temp_dir1 = tempfile.mkdtemp()
        temp_dir2 = tempfile.mkdtemp()
        try:
            file1 = request.files['file1']
            file2 = request.files['file2']
            file1_name = request.form.get('file1_name', 'file1')
            file2_name = request.form.get('file2_name', 'file2')

            # 保存文件到各自的临时目录
            file1_path = os.path.join(temp_dir1, file1.filename)
            file2_path = os.path.join(temp_dir2, file2.filename)
            file1.save(file1_path)
            file2.save(file2_path)

            # 获取文件扩展名
            ext = os.path.splitext(file1.filename)[1]

            # 调用文件比较函数
            status, result,_ = diffControl(file1_path, file2_path, file1_name, file2_name, ext)
            
            if status == 'ok':
                return jsonify({
                    'status': 'ok',
                    'diff_url': result
                })
            else:
                return jsonify({
                    'status': 'no',
                    'message': result
                }), 400

        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir1)
            shutil.rmtree(temp_dir2)
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