from flask import render_template
import model
import hashlib
import os
import csv_operations as csv_ops
import pandas as pd

DATA_FILE = 'data.csv'
DATA2_FILE = 'data2.csv'

def list():
    rows = model.fetch_everything_from_table(DATA_FILE)
    return render_template('test.html', rows=rows)

def copy_data_from_src_to_dest(src_file, dest_file):
    """复制并初始化数据文件"""
    try:
        # 直接复制文件而不是通过pandas处理
        if csv_ops.copy_csv(src_file, dest_file):
            print("Successfully copied data file")
            return True
        return False
    except Exception as e:
        print(f"Error copying data: {e}")
        return False

def update():
    rows = model.fetch_everything_from_table(DATA2_FILE)
    return render_template('test.html', rows=rows)

def hash(id):
    m = hashlib.md5()
    # 将字符串转换为字节
    m.update('gdkjssaklhd14252e8967bvsvvc'.encode('utf-8'))
    m.update(str(id).encode('utf-8'))
    return m.hexdigest()

def check_id(id):
    # Made the function less restrictive by changing the modulus
    if int(hash(id), 27) % 3 == 0:
        return True
    else:
        return False    

def convert_affairs_to_abc(df):
    """将Affairs数据转换为适合水印的格式"""
    # 使用affairs作为a列
    df['a'] = df['affairs']
    # 将age转为整数作为b列
    df['b'] = df['age'].astype(int)
    # 使用rating作为c列(因为我们需要对c进行位操作)
    df['c'] = df['rating'].astype(int)
    return df[['a', 'b', 'c']]

def load_watermark():
    """从文件加载水印序列
    读取watermark.txt文件获取水印比特序列，如果文件不存在则使用默认水印序列
    Returns:
        list: 水印比特序列[0,1,...]
    """
    try:
        with open('watermark.txt', 'r') as f:
            bits = f.read().strip().split(',')
            return [int(bit) for bit in bits]
    except FileNotFoundError:
        print("Warning: watermark.txt not found, using default watermark")
        return [1, 0, 1, 1, 0, 1, 0, 1]  # 默认水印

WATERMARK_BITS = load_watermark()
WATERMARK_BITS = load_watermark()

def get_watermark_bit(index):
    """获取水印序列中的特定位置的比特值
    Args:
        index: 位置索引
    Returns:
        int: 返回该位置的水印比特值(0或1)
    """
    return WATERMARK_BITS[index % len(WATERMARK_BITS)]

def watermark(filename):
    """使用差分扩展(DE)方法嵌入水印
    对数据行两两分组进行水印嵌入:
    1. 计算两行rating值的平均值l和差值h
    2. 如果差值在阈值范围内,使用DE方法:
       - h_embedded = 2h + watermark_bit
       - x_new = l + (h_embedded+1)/2
       - y_new = l - h_embedded/2
    3. 如果超出阈值范围,回退到LSB方法:
       - 直接修改最低位为水印比特
    
    Args:
        filename: 要嵌入水印的CSV文件
    Returns:
        bool: 嵌入是否成功
    """
    try:
        if not os.path.exists(filename):
            print(f"Error: {filename} does not exist")
            return False

        global WATERMARK_BITS
        WATERMARK_BITS = load_watermark()
        df = csv_ops.read_csv(filename)
        watermark_index = 0

        if 'original_rating1' not in df.columns or 'original_rating2' not in df.columns:
            df['original_rating1'] = None
            df['original_rating2'] = None

        if 'fallback1' not in df.columns:
            df['fallback1'] = 0
        if 'fallback2' not in df.columns:
            df['fallback2'] = 0

        max_h = 255  # Adjust according to rating range

        i = 0
        while watermark_index < len(WATERMARK_BITS) and i < len(df) - 1:
            if check_id(i+1):
                try:
                    x = int(df.loc[i, 'rating'])
                    y = int(df.loc[i+1, 'rating'])

                    # Save original values
                    df.at[i, 'original_rating1'] = x
                    df.at[i+1, 'original_rating2'] = y

                    l = (x + y) // 2
                    h = x - y

                    if abs(h) <= max_h:
                        bit = WATERMARK_BITS[watermark_index]
                        h_embedded = 2 * h + bit

                        x_new = l + (h_embedded + 1) // 2
                        y_new = l - h_embedded // 2

                        # If out of [0..255], fallback to LSB
                        if x_new < 0 or x_new > 255 or y_new < 0 or y_new > 255:
                            x_new = (x & ~1) | bit
                            y_new = (y & ~1) | bit
                            df.at[i, 'fallback1'] = 1
                            df.at[i+1, 'fallback2'] = 1

                        df.at[i, 'rating'] = x_new
                        df.at[i+1, 'rating'] = y_new

                        watermark_index += 1
                    else:
                        # fallback to LSB toggling
                        bit = WATERMARK_BITS[watermark_index]
                        x_new = (x & ~1) | bit
                        y_new = (y & ~1) | bit
                        df.at[i,'rating'] = x_new
                        df.at[i+1,'rating'] = y_new
                        df.at[i, 'fallback1'] = 1
                        df.at[i+1, 'fallback2'] = 1
                        watermark_index += 1
                except Exception as e:
                    print(f"Error processing rows {i+1} and {i+2}: {e}")
                    pass
            i += 1  # Move to the next record
        print(f"Total watermark bits embedded: {watermark_index}")
        return True
    except Exception as e:
        print(f"Error during watermarking: {e}")
        return False

def reverse_watermark(filename):
    """从文件中提取水印并恢复原始数据
    1. 遍历数据行两两分组
    2. 根据fallback标记判断使用何种方式提取:
       - 如果使用了DE方法,通过 h_embedded%2 获取水印位
       - 如果使用了LSB方法,直接获取最低位
    3. 恢复为保存的原始rating值
    
    Args:
        filename: 包含水印的CSV文件路径
    """
    df = csv_ops.read_csv(filename)
    max_h = 255  # Ensure max_h is defined here as well

    # Ensure columns exist to avoid KeyError
    if 'original_rating1' not in df.columns:
        df['original_rating1'] = None
    if 'original_rating2' not in df.columns:
        df['original_rating2'] = None

    if 'fallback1' not in df.columns:
        df['fallback1'] = 0
    if 'fallback2' not in df.columns:
        df['fallback2'] = 0

    try:
        extracted_bits = []

        i = 0
        while i < len(df) - 1 and len(extracted_bits) < len(WATERMARK_BITS):
            try:
                x = int(df.loc[i, 'rating'])
                y = int(df.loc[i+1, 'rating'])

                if df.loc[i,'fallback1'] == 1 and df.loc[i+1,'fallback2'] == 1:
                    bit = x & 1
                    extracted_bits.append(bit)
                else:
                    l = (x + y) // 2
                    h_embedded = x - y

                    if abs(h_embedded) <= 2 * max_h + 1:
                        bit = h_embedded % 2
                        h = (h_embedded - bit) // 2
                        extracted_bits.append(bit)
                    else:
                        # fallback: extract from LSB
                        bit = x & 1
                        extracted_bits.append(bit)

                # Restore original values if available
                if not pd.isna(df.loc[i, 'original_rating1']) and not pd.isna(df.loc[i+1, 'original_rating2']):
                    df.at[i, 'rating'] = int(df.loc[i, 'original_rating1'])
                    df.at[i+1, 'rating'] = int(df.loc[i+1, 'original_rating2'])
            except Exception as e:
                print(f"Error processing rows {i+1} and {i+2}: {e}")
                pass
            i += 1  # Move to the next record

        # Drop columns used for storing original values
        df.drop(columns=['original_rating1', 'original_rating2', 'fallback1', 'fallback2'], inplace=True, errors='ignore')

        csv_ops.write_csv(df, filename)
        print(f"Extracted watermark bits: {extracted_bits}")
    except Exception as e:
        print(f"Error during reverse watermark: {e}")

def extract_watermark(filename):
    """仅提取水印序列而不恢复数据
    Args:
        filename: 包含水印的CSV文件
    Returns:
        list: 提取出的水印比特序列
    """
    try:
        extracted_bits = []
        df = csv_ops.read_csv(filename)
        max_h = 255  # Ensure max_h is defined here as well

        # Ensure 'rating' exists to avoid KeyError
        if 'rating' not in df.columns:
            print("Error: 'rating' column not found")
            return []

        i = 0
        while i < len(df) - 1 and len(extracted_bits) < len(WATERMARK_BITS):
            try:
                x = int(df.loc[i, 'rating'])
                y = int(df.loc[i+1, 'rating'])
                h_embedded = x - y
                if abs(h_embedded) <= 2 * max_h + 1:
                    bit = h_embedded % 2
                else:
                    bit = x & 1
                extracted_bits.append(bit)
            except Exception as e:
                print(f"Error extracting bit at row {i+1}: {e}")
            i += 1
        print(f"Extracted watermark bits: {extracted_bits}")
        return extracted_bits
    except Exception as e:
        print(f"Error extracting watermark: {e}")
        return []

def count_similarity(list1, list2):
    """比较两个列表的数据相似度"""
    if not list1 or not list2:
        print("Error: Empty data list")
        return 0
        
    length = min(len(list1), len(list2))
    count = 0
    
    for i in range(length):
        try:
            if (float(list1[i][0]) == float(list2[i][0]) and 
                float(list1[i][1]) == float(list2[i][1]) and 
                float(list1[i][2]) == float(list2[i][2])):
                count += 1
        except (IndexError, ValueError) as e:
            print(f"Error comparing row {i}: {e}")
            continue

    per = (float(count)/length)*100
    diff = length-count
    print(f"Total rows: {length}")
    print(f"Total tuples not matched: {diff}")
    print(f"Similarity percentage: {per:.2f}%")
    return per        

def compare_tables(src, dest):
    """比较两个CSV文件的内容"""
    try:
        list1 = model.fetch_a_b_c_from_table(src)
        list2 = model.fetch_a_b_c_from_table(dest)
        if not list1 or not list2:
            print("Error: Could not fetch data from tables")
            return
        return count_similarity(list1, list2)
    except Exception as e:
        print(f"Error comparing tables: {e}")

if __name__ == '__main__':
    # 确保数据文件存在
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found")
        exit(1)

    while True:
        try:
            text = int(input('''Enter 1 for refreshing data2.csv from data.csv
Enter 2 for watermarking data2.csv
Enter 3 for comparing original and watermarked data
Enter 4 for extracting watermark
Enter 5 for showing embedded watermark
Enter 0 to exit\n'''))
            
            if text == 1:
                copy_data_from_src_to_dest(DATA_FILE, DATA2_FILE)
            elif text == 2:
                if os.path.exists(DATA2_FILE):
                    watermark(DATA2_FILE)
                else:
                    print("Please run option 1 first to initialize data2.csv")
            elif text == 3:
                compare_tables('data.csv', 'data2.csv')
            elif text == 4:
                reverse_watermark('data2.csv')
                print("Watermark extracted from data2.csv")
            elif text == 5:
                extracted = extract_watermark('data2.csv')
            elif text == 0:
                break
            else:
                print("Invalid option")
        except ValueError:
            print("Please enter a valid number")
        except Exception as e:
            print(f"Error: {e}")




