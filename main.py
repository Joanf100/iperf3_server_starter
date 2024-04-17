from queue import Queue
import subprocess
import threading
import time
import re

required_mbps = 20
n_servers = 20
refresh_rate = 1


def generate_iperf_commands(num_commands, start_port=5200):
    base_command = "stdbuf -oL -eL iperf3 -s -f m -p {}"
    commands = [base_command.format(port) for port in range(start_port, start_port + num_commands)]
    return commands


def manage_process_output(proce, proc_id, speed_queue):
    while True:
        line = proce.stdout.readline()

        pattern = r"\[\s*(\d+)\]\s+(\d+\.\d+)-(\d+\.\d+)\s+sec\s+(\d+\.\d+)\s+MBytes\s+(\d+\.\d+)\s+Mbits/sec"

        match = re.match(pattern, line)

        if match:
            index = match.group(1)
            time_1 = match.group(2)
            time_2 = match.group(3)
            data_amount = match.group(4)
            data_rate = match.group(5)
            result = {
                "did_end": False,
                "index": index,
                "time_1": time_1,
                "time_2": time_2,
                "data_transmitted": float(data_amount),
                "data_rate": float(data_rate),
                "pid": proc_id
            }
            speed_queue.put(result)

        connection_terminated = r"iperf3:\s+the\s+client\s+has\s+terminated"
        match = re.search(connection_terminated, line, re.IGNORECASE)

        if match:
            end_message = {
                "did_end": True,
                "pid": proc_id
            }

            speed_queue.put(end_message)

        if not line:
            break


processes = []
speed_queue = Queue()

commands = generate_iperf_commands(n_servers)

for i, cmd in enumerate(commands):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    thread = threading.Thread(target=manage_process_output, args=(proc, i, speed_queue))

    thread.start()

    processes.append((proc, thread))

try:
    print("iperf3 servers are running in the background...")
    best_speeds = []

    while True:
        while not speed_queue.empty():
            data = speed_queue.get()

            contains = False
            for item in best_speeds:
                if item["pid"] == data["pid"]:
                    if data["did_end"]:
                        item["data_rate"] = -1
                        item["did_end"] = True
                    else:
                        item["data_rate"] = data["data_rate"]
                        item["did_end"] = False

                    contains = True

            if not contains:
                best_speeds.append(data)
                best_speeds.sort(key=lambda x: x["pid"], reverse=False)

        did_print = False

        for item in best_speeds:
            did_print = True

            pid = item["pid"]

            if item["did_end"]:
                print(f"\033[31m" + f"_{pid}_:0|" + "\033[0m", end=" ")
            else:
                speed = item["data_rate"]

                if item["data_rate"] >= required_mbps:
                    print(f"\033[32m" + f"_{pid}_:{speed}|" + "\033[0m", end=" ")
                else:
                    print(f"\033[31m" + f"_{pid}_:{speed}|" + "\033[0m", end=" ")
        if did_print:
            print("")

        time.sleep(refresh_rate)

finally:
    for proc, _ in processes:
        proc.terminate()

    for _, thread in processes:
        thread.join()

    print("All iperf3 servers have been terminated.")
