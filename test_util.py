import requests
import time
import random
import psutil
import matplotlib.pyplot as plt

# 内网服务器配置server configuration
SERVER_IP = "121.43.52.68"
SERVER_PORT = 6001
BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

# 模拟任务生成Simulation task generation
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

# 实现任务调度算法Implement the task scheduling algorithm
def schedule_tasks(tasks, algorithm="Priority"):
    if algorithm == "Priority":
        return sorted(tasks, key=lambda x: x["priority"])  # 优先级越低越靠前
    elif algorithm == "FCFS":
        return sorted(tasks, key=lambda x: x["arrival_time"])
    elif algorithm == "SJF":
        return sorted(tasks, key=lambda x: x["processing_time"])
    else:
        raise ValueError("Unknown scheduling algorithm")

# 提交任务到内网服务器Submit the task to the Intranet server
def submit_task(task):
    try:
        payload = {
            "task_id": task["id"],
            "processing_time": task["processing_time"],
            "priority": task["priority"]
        }
        print(f"Submitting task with payload: {payload}")  # 打印请求的详细信息
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

# 监控任务状态Monitoring task status
def monitor_jobs(job_ids):
    completed_jobs = {}
    job_completion_times = {}
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

        # Record average response time for this interval
        if interval_response_times:
            avg_response_time = sum(interval_response_times) / len(interval_response_times)
        else:
            avg_response_time = 0
        response_times.append(avg_response_time)

        # Print a separator after each polling interval
        print("-" * 40)

        time.sleep(2)  # 轮询间隔polling interval
    return completed_jobs, job_completion_times, response_times

# 计算并绘制指标Plotting task states
def plot_metrics(metrics, algorithms, tasks):
    plt.figure(figsize=(15, 15))  # Increase the overall figure size

    for i, algorithm in enumerate(algorithms):
        job_completion_times, response_times = metrics[algorithm]

        # 计算周转时间、平均等待时间和平均响应时间
        turnaround_times = list(job_completion_times.values())
        avg_waiting_time = [turnaround_time - task["processing_time"] for task, turnaround_time in zip(tasks, turnaround_times)]
        avg_response_time = response_times

        plt.subplot(3, 1, 1)
        plt.plot(turnaround_times, label=f'Turnaround Time - {algorithm}', linewidth=2)
        plt.xlabel('Job Index')
        plt.ylabel('Turnaround Time (s)')
        plt.title('Turnaround Time')
        plt.legend()

        plt.subplot(3, 1, 2)
        plt.plot(avg_waiting_time, label=f'Average Waiting Time - {algorithm}', linewidth=2)
        plt.xlabel('Job Index')
        plt.ylabel('Average Waiting Time (s)')
        plt.title('Average Waiting Time')
        plt.legend()

        plt.subplot(3, 1, 3)
        plt.plot(avg_response_time, label=f'Average Response Time - {algorithm}', linewidth=2)
        plt.xlabel('Time (s)')
        plt.ylabel('Average Response Time (s)')
        plt.title('Average Response Time')
        plt.legend()

    plt.tight_layout()
    plt.show()

# 主函数main function
def main():
    # Step 1: 生成任务
    num_tasks = 10
    tasks = generate_tasks(num_tasks)
    print("Generated tasks:")
    for task in tasks:
        print(task)

    algorithms = ["FCFS", "SJF", "Priority"]
    metrics = {}

    for algorithm in algorithms:
        # Step 2: 选择调度算法
        print(f"\nScheduling tasks using {algorithm} algorithm...")
        scheduled_tasks = schedule_tasks(tasks, algorithm=algorithm)

        # Step 3: 提交任务
        job_ids = []
        for task in scheduled_tasks:
            job_id = submit_task(task)
            if job_id:
                job_ids.append(job_id)

        # Step 4: 监控任务状态
        print("\nMonitoring job statuses...")
        results, job_completion_times, response_times = monitor_jobs(job_ids)
        print("\nFinal job results:")
        for job_id, status in results.items():
            print(f"Job {job_id}: {status}")

        # Store metrics for plotting
        metrics[algorithm] = (job_completion_times, response_times)

    # Step 5: 绘制任务状态
    plot_metrics(metrics, algorithms, tasks)

if __name__ == "__main__":
    main()

