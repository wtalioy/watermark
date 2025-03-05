import csv_operations as csv_ops
import pandas as pd

def delete_everything_table(filename):
    df = pd.DataFrame(columns=['ID','a','b','c'])
    csv_ops.write_csv(df, filename)
    print("data deleted successfully")

def insert_param_into_table(dest_filename, rows):
    df = pd.DataFrame(rows, columns=['a','b','c'])
    df.index = df.index + 1  # 1-based indexing
    df.index.name = 'ID'
    csv_ops.write_csv(df, dest_filename)
    print("inserted successfully")

def fetch_everything_from_table(filename):
    df = csv_ops.read_csv(filename)
    return df.values.tolist()

def fetch_a_b_c_from_table(filename):
    """将原始数据转换为标准的a,b,c格式
    数据转换规则:
    - affairs 值转为 a 列
    - age 值转为 b 列
    - rating 值转为 c 列
    
    Args:
        filename: CSV文件路径
    Returns:
        list: 转换后的[a,b,c]格式数据列表
    """
    df = csv_ops.read_csv(filename)
    converted_df = pd.DataFrame()
    converted_df['a'] = df['affairs']
    converted_df['b'] = df['age'].astype(int)
    converted_df['c'] = df['rating'].astype(int)
    return converted_df[['a','b','c']].values.tolist()

def fetch_only_a_b_c_from_table(filename, id):
    """获取指定ID行的a,b,c值
    Args:
        filename: CSV文件路径或DataFrame对象
        id: 行ID(1-based)
    Returns:
        list: 该行的[a,b,c]值,出错则返回[0,0,0]
    """
    try:
        df = csv_ops.read_csv(filename)
        if id > len(df):
            raise IndexError(f"ID {id} is out of range")
        row = df.iloc[id-1]
        return [float(row['affairs']), float(row['age']), int(row['rating'])]
    except Exception as e:
        print(f"Error fetching row {id}: {e}")
        return [0, 0, 0]

def update_all_a_b_c_in_table(filename, params):
    """批量更新表中多行的a,b,c值
    支持原始affairs/age/rating列名和转换后的a/b/c列名
    
    Args:
        filename: CSV文件路径
        params: 包含(a,b,c,id)元组的列表
    """
    df = csv_ops.read_csv(filename)
    
    # 确定要更新的列名
    col_a = 'affairs' if 'affairs' in df.columns else 'a'
    col_b = 'age' if 'age' in df.columns else 'b'
    col_c = 'rating' if 'rating' in df.columns else 'c'
    
    for id, (a,b,c) in zip([p[3] for p in params], [(p[0],p[1],p[2]) for p in params]):
        # 确保数据类型正确
        row_idx = id-1
        df.at[row_idx, col_a] = float(a)
        df.at[row_idx, col_b] = float(b)
        df.at[row_idx, col_c] = int(c)
    
    csv_ops.write_csv(df, filename)
    print("Updated successfully")

def convert_to_abc_format(df):
    """将DataFrame转换为标准的a,b,c列格式
    Args:
        df: 包含原始数据的DataFrame
    Returns:
        DataFrame: 转换后的包含a,b,c列的DataFrame
    """
    abc_df = pd.DataFrame()
    abc_df['a'] = df['affairs']
    abc_df['b'] = df['age'].astype(int)
    abc_df['c'] = df['rating'].astype(int)
    return abc_df

def read_and_convert_data(filename):
    """读取并转换数据格式"""
    df = csv_ops.read_csv(filename)
    converted_df = pd.DataFrame()
    
    # 动态确定源列名
    col_a = 'affairs' if 'affairs' in df.columns else 'a'
    col_b = 'age' if 'age' in df.columns else 'b'
    col_c = 'rating' if 'rating' in df.columns else 'c'
    
    # 转换数据类型
    converted_df['a'] = pd.to_numeric(df[col_a], errors='coerce').fillna(0).astype(float)
    converted_df['b'] = pd.to_numeric(df[col_b], errors='coerce').fillna(0).astype(float)
    converted_df['c'] = pd.to_numeric(df[col_c], errors='coerce').fillna(0).astype(int)
    
    return converted_df

def fetch_only_a_b_c_from_table(df, id):
    """从DataFrame中获取值"""
    try:
        if isinstance(df, str):
            df = read_and_convert_data(df)
        
        row = df.iloc[id-1]
        
        if 'affairs' in df.columns:
            return [float(row['affairs']), float(row['age']), int(row['rating'])]
        else:
            return [float(row['a']), float(row['b']), int(row['c'])]
    except Exception as e:
        print(f"Error fetching row {id}: {e}")
        return [0, 0, 0]  # 返回默认值而不是抛出异常

if __name__ == '__main__':
    x=int(input('''Enter 1 for deleting every row from table
Enter 2 for inserting rows\n'''))
    y=str(input("Insert table name\n"))
    if x == 1:    
        delete_everything_table(y)    
    else:
        rows = [
            (1, 2, 3),
            (4, 5, 6),
            (7, 8, 9)
        ]
        insert_param_into_table(y, rows)




