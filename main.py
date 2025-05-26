from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import tempfile
import shutil
from dir_compare import DirectoryComparator
from control import generate_diff_report
from file2html import convert_to_html
import uuid
import hashlib
import filecmp
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Tuple, List

# 创建静态文件目录
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static",
    template_folder="public",
)

# 配置上传文件夹
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

CORS(app)


@app.route("/")
def index():
    return send_from_directory("public", "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("public", path)


def process_different_file(
    file_path: str, temp_dir1: str, temp_dir2: str
) -> Tuple[str, str]:
    """处理不同的文件，生成差异报告"""
    file1_path = os.path.join(temp_dir1, file_path)
    file2_path = os.path.join(temp_dir2, file_path)
    status, diff_content, _ = generate_diff_report(file1_path, file2_path)
    return file_path, diff_content if status == "ok" else None


def process_identical_file(
    file_path: str, temp_dir1: str, temp_dir2: str
) -> Tuple[str, str]:
    """处理相同的文件，生成HTML内容"""
    file1_path = os.path.join(temp_dir1, file_path)
    status, html_content = convert_to_html(file1_path)
    return file_path, html_content if status == "ok" else None


def process_single_file(file_path: str, temp_dir: str) -> Tuple[str, str]:
    """处理单个文件，生成HTML内容"""
    file_path_full = os.path.join(temp_dir, file_path)
    status, html_content = convert_to_html(file_path_full)
    return file_path, html_content if status == "ok" else None


@app.route("/api/compare", methods=["POST"])
def compare_directories():
    try:
        # 检查是否是单文件比对
        is_single_file = request.form.get("is_single_file") == "true"

        if is_single_file:
            # 单文件比对逻辑
            file1 = request.files["file1"]
            file2 = request.files["file2"]
            file1_name = request.form.get("file1_name")
            file2_name = request.form.get("file2_name")

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

            # 初始化变量
            diff_content = None
            html_content = None

            if identical:
                # 如果文件相同，只生成一份文件查看报告
                status, html_content = convert_to_html(file1_path)
                if status != "ok":
                    # 清理临时目录
                    shutil.rmtree(temp_dir1)
                    shutil.rmtree(temp_dir2)
                    return jsonify({"error": html_content}), 500
            else:
                # 如果文件不同，生成差异报告
                status, diff_content, _ = generate_diff_report(file1_path, file2_path)
                if status != "ok":
                    # 清理临时目录
                    shutil.rmtree(temp_dir1)
                    shutil.rmtree(temp_dir2)
                    return jsonify({"error": diff_content}), 500

            # 清理临时目录
            shutil.rmtree(temp_dir1)
            shutil.rmtree(temp_dir2)

            # 统一返回数据结构
            return jsonify(
                {
                    "is_single_file": True,
                    "comparison_results": {
                        "only_in_dir1": [],
                        "only_in_dir2": [],
                        "identical": [file1_name] if identical else [],
                        "different": [file1_name] if not identical else [],
                    },
                    "stats": {
                        "only_in_dir1": 0,
                        "only_in_dir2": 0,
                        "identical": 1 if identical else 0,
                        "different": 0 if identical else 1,
                    },
                    "diff_reports": {file1_name: diff_content} if diff_content else {},
                    "dir1_contents": {file1_name: {"html_content": html_content}},
                    "dir2_contents": {file2_name: {"html_content": html_content}},
                }
            )
        else:
            # 文件夹比对逻辑
            dir1_files = request.files.getlist("dir1")
            dir2_files = request.files.getlist("dir2")

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

            # 初始化结果字典
            diff_reports = {}
            dir1_contents = {}
            dir2_contents = {}

            # 使用线程池并行处理文件
            with ThreadPoolExecutor(
                max_workers=min(32, os.cpu_count() * 4)
            ) as executor:
                # 处理不同的文件
                diff_futures = {
                    executor.submit(
                        process_different_file, file_path, temp_dir1, temp_dir2
                    ): file_path
                    for file_path in results["different"]
                }

                # 处理相同的文件
                identical_futures = {
                    executor.submit(
                        process_identical_file, file_path, temp_dir1, temp_dir2
                    ): file_path
                    for file_path in results["identical"]
                }

                # 处理只在dir1中的文件
                dir1_futures = {
                    executor.submit(
                        process_single_file, file_path, temp_dir1
                    ): file_path
                    for file_path in results["only_in_dir1"]
                }

                # 处理只在dir2中的文件
                dir2_futures = {
                    executor.submit(
                        process_single_file, file_path, temp_dir2
                    ): file_path
                    for file_path in results["only_in_dir2"]
                }

                # 收集所有结果
                for future in as_completed(diff_futures):
                    file_path, diff_content = future.result()
                    if diff_content:
                        diff_reports[file_path] = diff_content

                for future in as_completed(identical_futures):
                    file_path, html_content = future.result()
                    if html_content:
                        dir1_contents[file_path] = {"html_content": html_content}
                        dir2_contents[file_path] = {"html_content": html_content}

                for future in as_completed(dir1_futures):
                    file_path, html_content = future.result()
                    if html_content:
                        dir1_contents[file_path] = {"html_content": html_content}

                for future in as_completed(dir2_futures):
                    file_path, html_content = future.result()
                    if html_content:
                        dir2_contents[file_path] = {"html_content": html_content}

            # 计算统计信息
            stats = {
                "only_in_dir1": len(results["only_in_dir1"]),
                "only_in_dir2": len(results["only_in_dir2"]),
                "identical": len(results["identical"]),
                "different": len(results["different"]),
            }

            # 清理临时目录
            shutil.rmtree(temp_dir1)
            shutil.rmtree(temp_dir2)

            # 在返回结果前打印最终的数据
            print("\n=== 最终返回的数据 ===")
            print(f"diff_reports中的文件: {list(diff_reports.keys())}")
            print(f"dir1_contents中的文件: {list(dir1_contents.keys())}")
            print(f"dir2_contents中的文件: {list(dir2_contents.keys())}")

            # 确保在返回结果前，所有内容都已经生成
            if not all(file_path in diff_reports for file_path in results["different"]):
                print("\n警告: 部分文件的差异报告未生成")
                missing_files = set(results["different"]) - set(diff_reports.keys())
                print(f"缺失的文件: {missing_files}")

            return jsonify(
                {
                    "is_single_file": False,
                    "comparison_results": {
                        "only_in_dir1": results["only_in_dir1"],
                        "only_in_dir2": results["only_in_dir2"],
                        "identical": results["identical"],
                        "different": results["different"],
                    },
                    "stats": stats,
                    "diff_reports": diff_reports,
                    "dir1_contents": dir1_contents,
                    "dir2_contents": dir2_contents,
                }
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # 生产环境配置
    app.run(host='0.0.0.0', port=5000, debug=False)
