import random
import sys
import pandas as pd

def generate_parameters():
    params = []
    for i in range(1, 10000):
        a = random.randint(1, 10000)
        b = random.randint(1, 10000)
        c = random.randint(1, 10000)
        temp = sys.maxsize  # 替换 maxint 为 maxsize
        c = c & (temp ^ 2)  # unsetting 2nd bit
        c = c & (temp ^ 8)  # unsetting 4th bit
        params.append((a, b, c))
    return params

def generate_csv(filename):
    """生成CSV文件并保存"""
    params = generate_parameters()
    df = pd.DataFrame(params, columns=['a', 'b', 'c'])
    df.index = df.index + 1  # 1-based indexing
    df.index.name = 'ID'
    df.to_csv(filename)
    print(f"Generated data saved to {filename}")

def check_bit(num):
    return bool(((num >> 1) & 1) & ((num >> 3) & 1))

def check_bit_unset(rows):
    found = False
    for x in rows:
        if check_bit(x[2]):
            print(x[2])
            found = True
    
    if not found:
        print("No numbers found")

if __name__ == '__main__':
    action = input('''Enter 1 to generate new CSV file
Enter 2 to check bit patterns in existing data\n''')
    
    if action == '1':
        filename = input("Enter output CSV filename: ")
        generate_csv(filename)
    else:
        filename = input("Enter CSV file to check: ")
        df = pd.read_csv(filename)
        params = df[['a','b','c']].values.tolist()
        check_bit_unset(params)
