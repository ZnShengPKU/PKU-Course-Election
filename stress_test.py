#!/usr/bin/env python3
"""
CourseElection 压力测试脚本
模拟并发用户访问，监控性能和内存使用
"""

import requests
import time
import threading
import psutil
import statistics
from datetime import datetime
from collections import defaultdict

# 配置
TARGET_URL = "http://localhost:8502"
HEALTH_CHECK_URL = f"{TARGET_URL}/_stcore/health"
CONCURRENT_USERS = 100  # 并发用户数
REQUESTS_PER_USER = 5  # 每个用户的请求数
DELAY_BETWEEN_REQUESTS = 0.5  # 请求间隔（秒）

# 存储测试结果
results = {
    'response_times': [],
    'errors': [],
    'status_codes': defaultdict(int),
    'memory_samples': []
}

# 线程锁
lock = threading.Lock()

def get_streamlit_process():
    """找到Streamlit进程"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'streamlit' in cmdline and 'app.py' in cmdline:
                return psutil.Process(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def monitor_memory(process, duration=30, interval=1):
    """监控进程内存使用"""
    start_time = time.time()
    memory_samples = []
    
    while time.time() - start_time < duration:
        try:
            mem_info = process.memory_info()
            memory_mb = mem_info.rss / (1024 * 1024)  # 转换为MB
            memory_samples.append(memory_mb)
            with lock:
                results['memory_samples'].append({
                    'timestamp': time.time(),
                    'memory_mb': memory_mb
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            break
        time.sleep(interval)
    
    return memory_samples

def simulate_user(user_id):
    """模拟单个用户的访问行为"""
    user_results = []
    
    for req_num in range(REQUESTS_PER_USER):
        try:
            start_time = time.time()
            
            # 发送请求
            response = requests.get(
                TARGET_URL,
                timeout=10,
                headers={
                    'User-Agent': f'StressTest-User-{user_id}',
                    'Accept': 'text/html,application/xhtml+xml'
                }
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 记录结果
            with lock:
                results['response_times'].append(response_time)
                results['status_codes'][response.status_code] += 1
            
            user_results.append({
                'user_id': user_id,
                'request_num': req_num + 1,
                'status_code': response.status_code,
                'response_time': response_time,
                'success': response.status_code == 200
            })
            
            # 请求间延迟
            if req_num < REQUESTS_PER_USER - 1:
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
        except requests.exceptions.Timeout:
            with lock:
                results['errors'].append(f'User {user_id} - Request {req_num + 1}: Timeout')
            user_results.append({
                'user_id': user_id,
                'request_num': req_num + 1,
                'error': 'Timeout'
            })
            
        except Exception as e:
            with lock:
                results['errors'].append(f'User {user_id} - Request {req_num + 1}: {str(e)}')
            user_results.append({
                'user_id': user_id,
                'request_num': req_num + 1,
                'error': str(e)
            })
    
    return user_results

def run_stress_test():
    """运行压力测试"""
    print("=" * 70)
    print("CourseElection 压力测试")
    print("=" * 70)
    print()
    
    # 检查服务是否运行
    print(f"1. 检查服务状态...")
    try:
        health_response = requests.get(HEALTH_CHECK_URL, timeout=5)
        if health_response.text.strip() == "ok":
            print("   ✓ 服务运行正常")
        else:
            print(f"   ✗ 服务状态异常: {health_response.text}")
            return
    except Exception as e:
        print(f"   ✗ 无法连接到服务: {str(e)}")
        return
    
    print()
    
    # 找到Streamlit进程
    print(f"2. 定位Streamlit进程...")
    process = get_streamlit_process()
    if not process:
        print("   ✗ 找不到Streamlit进程")
        print("   提示: 请确保服务正在运行")
        return
    
    print(f"   ✓ 找到进程 PID: {process.pid}")
    
    # 记录初始内存
    initial_memory = process.memory_info().rss / (1024 * 1024)
    print(f"   初始内存使用: {initial_memory:.2f} MB")
    print()
    
    # 启动内存监控线程
    print(f"3. 启动内存监控...")
    test_duration = (REQUESTS_PER_USER * DELAY_BETWEEN_REQUESTS + 10)
    monitor_thread = threading.Thread(
        target=monitor_memory,
        args=(process, test_duration, 0.5)
    )
    monitor_thread.daemon = True
    monitor_thread.start()
    print(f"   ✓ 监控已启动（持续 {test_duration:.0f} 秒）")
    print()
    
    # 创建并发用户线程
    print(f"4. 启动压力测试...")
    print(f"   并发用户数: {CONCURRENT_USERS}")
    print(f"   每用户请求数: {REQUESTS_PER_USER}")
    print(f"   总请求数: {CONCURRENT_USERS * REQUESTS_PER_USER}")
    print(f"   请求间隔: {DELAY_BETWEEN_REQUESTS}s")
    print()
    
    start_test_time = time.time()
    
    # 创建线程
    threads = []
    for user_id in range(1, CONCURRENT_USERS + 1):
        thread = threading.Thread(target=simulate_user, args=(user_id,))
        threads.append(thread)
    
    # 启动所有线程
    print("   开始发送请求...")
    for thread in threads:
        thread.start()
        time.sleep(0.1)  # 轻微错开启动时间
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    end_test_time = time.time()
    test_duration_actual = end_test_time - start_test_time
    
    # 等待内存监控完成
    monitor_thread.join(timeout=5)
    
    print("   ✓ 测试完成")
    print()
    
    # 分析结果
    print("=" * 70)
    print("测试结果")
    print("=" * 70)
    print()
    
    # 响应时间统计
    if results['response_times']:
        response_times = results['response_times']
        print(f"📊 响应时间统计:")
        print(f"   总请求数:     {len(response_times)}")
        print(f"   平均响应时间: {statistics.mean(response_times):.3f}s")
        print(f"   最快响应:     {min(response_times):.3f}s")
        print(f"   最慢响应:     {max(response_times):.3f}s")
        print(f"   中位数:       {statistics.median(response_times):.3f}s")
        if len(response_times) > 1:
            print(f"   标准差:       {statistics.stdev(response_times):.3f}s")
        print()
    
    # HTTP状态码统计
    print(f"📋 HTTP状态码分布:")
    for code, count in sorted(results['status_codes'].items()):
        print(f"   {code}: {count} 次")
    print()
    
    # 错误统计
    if results['errors']:
        print(f"❌ 错误统计 ({len(results['errors'])} 个):")
        for error in results['errors'][:10]:  # 只显示前10个
            print(f"   - {error}")
        if len(results['errors']) > 10:
            print(f"   ... 还有 {len(results['errors']) - 10} 个错误")
        print()
    else:
        print(f"✅ 无错误")
        print()
    
    # 内存统计
    if results['memory_samples']:
        memory_values = [s['memory_mb'] for s in results['memory_samples']]
        final_memory = memory_values[-1]
        max_memory = max(memory_values)
        avg_memory = statistics.mean(memory_values)
        memory_increase = final_memory - initial_memory
        
        print(f"💾 内存使用统计:")
        print(f"   初始内存:     {initial_memory:.2f} MB")
        print(f"   最终内存:     {final_memory:.2f} MB")
        print(f"   最大内存:     {max_memory:.2f} MB")
        print(f"   平均内存:     {avg_memory:.2f} MB")
        print(f"   内存增长:     {memory_increase:+.2f} MB ({(memory_increase/initial_memory*100):+.1f}%)")
        print()
    
    # 性能指标
    total_requests = CONCURRENT_USERS * REQUESTS_PER_USER
    successful_requests = results['status_codes'].get(200, 0)
    success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
    requests_per_second = total_requests / test_duration_actual
    
    print(f"⚡ 性能指标:")
    print(f"   测试持续时间: {test_duration_actual:.2f}s")
    print(f"   成功率:       {success_rate:.1f}%")
    print(f"   吞吐量:       {requests_per_second:.2f} 请求/秒")
    print()
    
    # 性能评级
    print(f"📈 性能评级:")
    avg_response = statistics.mean(response_times) if response_times else 999
    
    if avg_response < 0.5 and success_rate >= 99:
        rating = "🟢 优秀"
        comment = "响应快速，稳定性好"
    elif avg_response < 1.0 and success_rate >= 95:
        rating = "🟢 良好"
        comment = "性能良好，可接受"
    elif avg_response < 2.0 and success_rate >= 90:
        rating = "🟡 一般"
        comment = "性能一般，建议优化"
    else:
        rating = "🔴 较差"
        comment = "需要性能优化"
    
    print(f"   评级: {rating}")
    print(f"   评价: {comment}")
    print()
    
    # 保存详细报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"stress_test_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"CourseElection 压力测试报告\n")
        f.write(f"{'=' * 70}\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"并发用户: {CONCURRENT_USERS}\n")
        f.write(f"每用户请求数: {REQUESTS_PER_USER}\n")
        f.write(f"总请求数: {total_requests}\n")
        f.write(f"\n")
        f.write(f"响应时间: {statistics.mean(response_times):.3f}s (平均)\n")
        f.write(f"成功率: {success_rate:.1f}%\n")
        f.write(f"内存使用: {initial_memory:.2f} MB → {final_memory:.2f} MB ({memory_increase:+.2f} MB)\n")
        f.write(f"\n")
        f.write(f"详细内存采样:\n")
        for sample in results['memory_samples']:
            f.write(f"  {sample['memory_mb']:.2f} MB\n")
    
    print(f"📄 详细报告已保存到: {report_file}")
    print()
    print("=" * 70)

if __name__ == "__main__":
    try:
        run_stress_test()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试出错: {str(e)}")
        import traceback
        traceback.print_exc()

