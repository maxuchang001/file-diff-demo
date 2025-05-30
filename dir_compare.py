import os
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional, Union
from file2html import convert_to_html

class DirectoryComparator:
    """目录比较工具类，用于比较两个目录的差异"""
    
    def __init__(self, dir1: str, dir2: str, exclude_patterns: Optional[List[str]] = None):
        """初始化目录比较工具
        
        Args:
            dir1: 第一个目录的路径
            dir2: 第二个目录的路径
            exclude_patterns: 要排除的文件或目录模式列表
        """
        self.dir1 = os.path.abspath(dir1)
        self.dir2 = os.path.abspath(dir2)
        self.exclude_patterns = exclude_patterns or []
        self.dir1_contents = {}
        self.dir2_contents = {}
        self.comparison_results = {
            'only_in_dir1': [],
            'only_in_dir2': [],
            'identical': [],
            'different': []
        }
        self.diff_dir = os.path.join(os.path.dirname(__file__), 'static', 'diffs')
        os.makedirs(self.diff_dir, exist_ok=True)

    def should_exclude(self, path: str) -> bool:
        """判断是否应排除该路径
        
        Args:
            path: 要检查的路径
            
        Returns:
            bool: 如果路径应该被排除返回True，否则返回False
        """
        for pattern in self.exclude_patterns:
            if pattern in path:
                return True
        return False

    def calculate_hash(self, file_path: str) -> Optional[str]:
        """计算文件的SHA-256哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件的SHA-256哈希值，如果计算失败则返回None
        """
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"Error hashing {file_path}: {e}")
            return None

    def scan_directory(self, directory: str) -> Dict[str, Dict]:
        """扫描目录并生成文件内容字典
        
        Args:
            directory: 要扫描的目录路径
            
        Returns:
            Dict: 包含目录内容的字典
        """
        contents = {}
        for root, dirs, files in os.walk(directory):
            for d in dirs:
                dir_path = os.path.join(root, d)
                rel_path = os.path.relpath(dir_path, directory)
                if self.should_exclude(rel_path):
                    continue
                contents[rel_path] = {
                    'type': 'directory',
                    'path': dir_path
                }
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, directory)
                if self.should_exclude(rel_path):
                    continue
                file_hash = self.calculate_hash(file_path)
                if file_hash:
                    contents[rel_path] = {
                        'type': 'file',
                        'hash': file_hash,
                        'size': os.path.getsize(file_path),
                        'mtime': os.path.getmtime(file_path),
                        'path': file_path
                    }
        return contents

    def compare(self) -> Dict:
        """比较两个目录的内容
        
        Returns:
            Dict: 包含比较结果的字典，只包含四个字段：
                - only_in_dir1: 仅在目录1中存在的文件
                - only_in_dir2: 仅在目录2中存在的文件
                - identical: 两个目录中相同的文件
                - different: 两个目录中不同的文件
        """
        print(f"Scanning directory {self.dir1}...")
        dir1_contents = self.scan_directory(self.dir1)
        print(f"Scanning directory {self.dir2}...")
        dir2_contents = self.scan_directory(self.dir2)

        print("Comparing directories...")
        all_rel_paths = set(dir1_contents.keys()).union(set(dir2_contents.keys()))

        # 比较每个文件
        for rel_path in sorted(all_rel_paths):
            in_dir1 = rel_path in dir1_contents
            in_dir2 = rel_path in dir2_contents

            if in_dir1 and not in_dir2:
                self.comparison_results['only_in_dir1'].append(rel_path)
            elif in_dir2 and not in_dir1:
                self.comparison_results['only_in_dir2'].append(rel_path)
            else:
                if dir1_contents[rel_path]['type'] == 'directory' and dir2_contents[rel_path]['type'] == 'directory':
                    continue
                elif dir1_contents[rel_path]['type'] == 'file' and dir2_contents[rel_path]['type'] == 'file':
                    hash1 = dir1_contents[rel_path]['hash']
                    hash2 = dir2_contents[rel_path]['hash']
                    if hash1 == hash2:
                        self.comparison_results['identical'].append(rel_path)
                    else:
                        self.comparison_results['different'].append(rel_path)
                else:
                    self.comparison_results['different'].append(rel_path)

        # 返回结果
        return {
            'only_in_dir1': self.comparison_results['only_in_dir1'],
            'only_in_dir2': self.comparison_results['only_in_dir2'],
            'identical': self.comparison_results['identical'],
            'different': self.comparison_results['different']
        }

    def generate_report(self) -> Dict:
        """生成比较报告
        
        Returns:
            Dict: 包含比较报告的字典
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'directory1': self.dir1,
            'directory2': self.dir2,
            'comparison_results': self.comparison_results,
            'stats': {
                'only_in_dir1': len(self.comparison_results['only_in_dir1']),
                'only_in_dir2': len(self.comparison_results['only_in_dir2']),
                'identical': len(self.comparison_results['identical']),
                'different': len(self.comparison_results['different']),
                'total_files_directories': len(set(self.dir1_contents.keys()).union(set(self.dir2_contents.keys())))
            }
        }

    def save_report(self, output_file: str) -> bool:
        """保存报告到JSON文件
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            bool: 如果保存成功返回True，否则返回False
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.generate_report(), f, indent=2, ensure_ascii=False)
            print(f"\nReport saved to {output_file}")
            return True
        except Exception as e:
            print(f"Error saving report to {output_file}: {e}")
            return False

    def print_results(self) -> None:
        """打印比较结果"""
        print(f"\nComparison results between {self.dir1} and {self.dir2}:")

        categories = [
            ('only_in_dir1', f"Files/Directories only in {self.dir1}"),
            ('only_in_dir2', f"Files/Directories only in {self.dir2}"),
            ('identical', "Identical files/directories in both directories"),
            ('different', "Files/Directories with same name but different content/type")
        ]

        for key, title in categories:
            items = self.comparison_results[key]
            if items:
                print(f"\n{title} ({len(items)}):")
                for item in items:
                    if key in ['only_in_dir1', 'only_in_dir2']:
                        full_path = os.path.join(self.dir1 if key == 'only_in_dir1' else self.dir2, item)
                    else:
                        full_path = item
                    print(f"  - {full_path}") 