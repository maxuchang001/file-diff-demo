from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import tempfile
import shutil
from dir_compare import DirectoryComparator
from control import diffControl

# 创建静态文件目录
static_dir = os.path.join(os.path.dirname(__file__), 'static')
diffs_dir = os.path.join(static_dir, 'diffs')
os.makedirs(diffs_dir, exist_ok=True)

app = Flask(__name__, 
           static_folder='static',
           static_url_path='/static',
           template_folder='public')

CORS(app)

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)

@app.route('/api/compare', methods=['POST'])
def compare():
    try:
        # 创建两个临时目录
        temp_dir1 = tempfile.mkdtemp()
        temp_dir2 = tempfile.mkdtemp()
        try:
            # 保存dir1文件
            for file in request.files.getlist('dir1'):
                rel_path = file.filename
                save_path = os.path.join(temp_dir1, rel_path)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                file.save(save_path)
            # 保存dir2文件
            for file in request.files.getlist('dir2'):
                rel_path = file.filename
                save_path = os.path.join(temp_dir2, rel_path)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                file.save(save_path)
            # 比较目录
            comparator = DirectoryComparator(temp_dir1, temp_dir2)
            result = comparator.compare()
            return jsonify(result)
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir1)
            shutil.rmtree(temp_dir2)
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
            status, result = diffControl(file1_path, file2_path, file1_name, file2_name, ext)
            
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)