import pandas as pd
import shutil
import os

def read_csv(filename):
    try:
        # 读取CSV时保留原始数据类型
        return pd.read_csv(filename, dtype={
            'affairs': float,
            'age': float,
            'rating': int,
            'a': float,
            'b': float,
            'c': int
        })
    except:
        # 如果指定类型失败，使用默认类型读取
        return pd.read_csv(filename)

def write_csv(df, filename):
    df.to_csv(filename, index=False)

def copy_csv(src, dest):
    """安全地复制CSV文件"""
    try:
        shutil.copy2(src, dest)
        return True
    except Exception as e:
        print(f"Error copying file: {e}")
        return False

def ensure_file_exists(filename, template_file):
    """确保文件存在，如果不存在则从模板复制"""
    if not os.path.exists(filename):
        return copy_csv(template_file, filename)
    return True

def update_rows(df, indices, new_values):
    """
    更新DataFrame中特定索引的行
    indices: 行号列表 (1-based)
    new_values: 包含(a,b,c)新值的元组列表
    """
    for idx, values in zip(indices, new_values):
        df.loc[idx-1, ['a','b','c']] = values
    return df
