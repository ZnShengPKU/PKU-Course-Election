#!/usr/bin/env python3
"""
数据格式转换工具
将Excel格式转换为Parquet格式以提升读取速度
"""

import pandas as pd
import os
from pathlib import Path

def convert_excel_to_parquet():
    """将Excel课程数据转换为Parquet格式"""
    
    excel_file = "课表信息汇总.xlsx"
    parquet_file = "courses.parquet"
    
    print(f"正在读取 {excel_file}...")
    
    if not os.path.exists(excel_file):
        print(f"错误: 找不到文件 {excel_file}")
        return False
    
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_file)
        print(f"✓ 成功读取 {len(df)} 条原始记录")
        
        # 预处理：合并相同课程号+班号的记录
        print("正在处理数据...")
        grouped = df.groupby(['课程号', '班号'], as_index=False)
        
        processed_data = []
        for _, group in grouped:
            # 获取第一行作为基础
            row = group.iloc[0].copy()
            
            # 合并修读对象
            if len(group) > 1:
                row['修读对象'] = '，'.join(group['修读对象'].astype(str).unique())
            
            processed_data.append(row)
        
        result_df = pd.DataFrame(processed_data)
        print(f"✓ 处理完成，共 {len(result_df)} 条课程记录")
        
        # 保存为Parquet格式
        print(f"正在保存为 {parquet_file}...")
        result_df.to_parquet(parquet_file, compression='snappy', index=False)
        
        # 获取文件大小对比
        excel_size = os.path.getsize(excel_file) / (1024 * 1024)  # MB
        parquet_size = os.path.getsize(parquet_file) / (1024 * 1024)  # MB
        
        print(f"\n✓ 转换成功!")
        print(f"  Excel文件大小:   {excel_size:.2f} MB")
        print(f"  Parquet文件大小: {parquet_size:.2f} MB")
        print(f"  空间节省:        {((excel_size - parquet_size) / excel_size * 100):.1f}%")
        print(f"\n预期读取速度提升: 5-10倍")
        
        return True
        
    except Exception as e:
        print(f"错误: 转换失败 - {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CourseElection 数据格式转换工具")
    print("=" * 60)
    print()
    
    success = convert_excel_to_parquet()
    
    if success:
        print("\n下次启动应用时将自动使用Parquet格式，加载速度更快！")
    else:
        print("\n转换失败，请检查错误信息")
