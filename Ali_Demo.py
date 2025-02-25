import requests
import time
import random
import psutil
import matplotlib.pyplot as plt

# 服务器配置
SERVER_IP = "121.43.52.68"
SERVER_PORT = 6001
BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

# 模拟任务生成
def generate_tasks(num_tasks=10):
    tasks = []
    current_time = time.time()
    for i in range(num_tasks):
        arrival_time = current_time + random.randint(0, 10)  # 随机生成到达时间
        tasks.append({
            "id": f"task_{i}",
            "processing_time": random.randint(1, 20),  # 随机生成处理时间
            "priority": random.randint(1, 10),         # 随机生成优先级
            "arrival_time": arrival_time               # 记录任务生成的时间戳
        })
    return tasks

# 实现任务调度算法
def schedule_tasks(tasks, algorithm="Priority"):
    if algorithm == "Priority":
        return sorted(tasks, key=lambda x: x["priority"])  # 优先级越低越靠前
    elif algorithm == "FCFS":
        return sorted(tasks, key=lambda x: x["arrival_time"])
    elif algorithm == "SJF":
        return sorted(tasks, key=lambda x: x["processing_time"])
    else:
        raise ValueError("Unknown scheduling algorithm")

# 提交任务到内网服务器
def submit_task(task):
    try:
        payload = {
            "task_id": task["id"],
            "processing_time": task["processing_time"],
            "priority": task["priority"]
        }
        print(f"Submitting task with payload: {payload}")  # 打印请求的详细信息Print the request details
        response = requests.post(
            f"{BASE_URL}/submit_task",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        print(f"Task {task['id']} submitted. Server Response: {result}")
        return result["job_id"]
    except Exception as e:
        print(f"Failed to submit task {task['id']}: {e}")
        return None

# 监控任务状态
def monitor_jobs(job_ids):
    completed_jobs = {}
    job_completion_times = {}
    cpu_usages = []
    memory_usages = []
    response_times = []
    start_time = time.time()
    while len(completed_jobs) < len(job_ids):
        interval_response_times = []
        for job_id in job_ids:
            if job_id in completed_jobs:
                continue
            try:
                request_start_time = time.time()
                response = requests.get(f"{BASE_URL}/job_status/{job_id}")
                response.raise_for_status()
                request_end_time = time.time()
                interval_response_times.append(request_end_time - request_start_time)

                result = response.json()
                status = result["status"]
                print(f"Job {job_id} status: {status}")
                if status in ["SUCCEEDED", "FAILED"]:
                    completed_jobs[job_id] = status
                    job_completion_times[job_id] = time.time() - start_time
            except Exception as e:
                print(f"Failed to fetch status for job {job_id}: {e}")

        # Record system usage
        cpu_usages.append(psutil.cpu_percent(interval=None))
        memory_usages.append(psutil.virtual_memory().percent)

        # Record average response time for this interval
        if interval_response_times:
            avg_response_time = sum(interval_response_times) / len(interval_response_times)
        else:
            avg_response_time = 0
        response_times.append(avg_response_time)

        # Print a separator after each polling interval
        print("-" * 40)

        time.sleep(2)  # 轮询间隔
    return completed_jobs, job_completion_times, cpu_usages, memory_usages, response_times

# 绘制任务状态
def plot_metrics(job_completion_times, cpu_usages, memory_usages, response_times):
    job_ids = list(job_completion_times.keys())
    completion_times = list(job_completion_times.values())

    plt.figure(figsize=(15, 15))  # Increase the overall figure size

    plt.subplot(3, 1, 1)
    plt.bar(job_ids, completion_times)
    plt.xlabel('Job ID')
    plt.ylabel('Completion Time (s)')
    plt.title('Job Completion Times')
    plt.xticks(rotation=45)  # Rotate x-axis labels to prevent overlapping

    plt.subplot(3, 1, 2)
    plt.plot(cpu_usages, label='CPU Usage (%)', linewidth=2)  # Increase line width
    plt.plot(memory_usages, label='Memory Usage (%)', linewidth=2)  # Increase line width
    plt.xlabel('Time (s)')
    plt.ylabel('Usage (%)')
    plt.title('CPU and Memory Usage Over Time')
    plt.legend()

    plt.subplot(3, 1, 3)
    plt.plot(response_times, label='Average Response Time (s)', linewidth=2)  # Increase line width
    plt.xlabel('Time (s)')
    plt.ylabel('Response Time (s)')
    plt.title('Average Response Time Over Time')
    plt.legend()

    plt.tight_layout()
    plt.show()

# 主函数main func.
def main():
    # Step 1: 生成任务generate tasks
    num_tasks = 10
    tasks = generate_tasks(num_tasks)
    print("Generated tasks:")
    for task in tasks:
        print(task)

    # Step 2: 选择调度算法choose scheduling alg.
    algorithm = "Priority"  # 可修改为 "FCFS" 或 "SJF" can change to “FCFS”/"SJF"
    print(f"\nScheduling tasks using {algorithm} algorithm...")
    scheduled_tasks = schedule_tasks(tasks, algorithm=algorithm)

    # Step 3: 提交任务submit the tasks
    job_ids = []
    for task in scheduled_tasks:
        job_id = submit_task(task)
        if job_id:
            job_ids.append(job_id)

    # Step 4: 监控任务状态monitor the task status
    print("\nMonitoring job statuses...")
    results, job_completion_times, cpu_usages, memory_usages, response_times = monitor_jobs(job_ids)
    print("\nFinal job results:")
    for job_id, status in results.items():
        print(f"Job {job_id}: {status}")

    # Display CPU, memory, and response time metrics
    print("\nCPU Usage (%):", cpu_usages)
    print("Memory Usage (%):", memory_usages)
    print("Average Response Times (s):", response_times)

    # Step 5: 绘制任务状态plot
    plot_metrics(job_completion_times, cpu_usages, memory_usages, response_times)

if __name__ == "__main__":
    main()