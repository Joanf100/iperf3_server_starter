from queue import Queue
import subprocess
import threading
import time

required_mbps = 20

# Define the iperf3 commands to be executed
commands = [
    'stdbuf -oL -eL iperf3 -s -p 5200',
    'stdbuf -oL -eL iperf3 -s -p 5201',
    'stdbuf -oL -eL iperf3 -s -p 5202',
    'stdbuf -oL -eL iperf3 -s -p 5203',
    'stdbuf -oL -eL iperf3 -s -p 5204',
    'stdbuf -oL -eL iperf3 -s -p 5205',
    'stdbuf -oL -eL iperf3 -s -p 5206',
    'stdbuf -oL -eL iperf3 -s -p 5207',
    'stdbuf -oL -eL iperf3 -s -p 5208',
    'stdbuf -oL -eL iperf3 -s -p 5209'
]


def manage_process_output(proce, proc_id, speed_queue):
    while True:
        line = proce.stdout.readline()
        if not line:
            break  # No more output

        if "[SUM]" in line:
            # Split the string by spaces and filter out empty strings
            parts = [part for part in line.split(" ") if part]
            # The desired output should be the second last element, based on the provided structure
            speed_value = float(parts[-3])
            speed_type = parts[-2]
            speed_final = parts[-1]

            if "sender" not in speed_final and "receiver" not in speed_final:
                if speed_type == "Gbits/sec":
                    speed_value *= 1000
                speed_queue.put({
                  "speed": speed_value,
                  "type": "Mbits/sec",
                  "didEnd": False,
                  "pid": proc_id
                })
            else:
                speed_queue.put({
                    "speed": 0,
                    "type": "N/A",
                    "didEnd": True,
                    "pid": proc_id
                })


processes = []
speed_queue = Queue()

for i, cmd in enumerate(commands):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    # Start a thread to handle this process's output
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
                    item["speed"] = data["speed"]
                    contains = True
                if data["speed"] == 0:
                    contains = True

            if not contains:
                best_speeds.append(data)
                best_speeds.sort(key=lambda x: x["pid"], reverse=False)

        for item in best_speeds:
            pid = item["pid"]
            speed = item["speed"]

            if item["speed"] >= required_mbps:
                print(f"\033[32m" + f"D_{pid}: {speed} |" + "\033[0m", end=" ")
            else:
                print(f"\033[31m" + f"D_{pid}: {speed} |" + "\033[0m", end=" ")

        print(" ")

        time.sleep(1)

finally:
    # Ensure all iperf3 servers are terminated
    for proc, _ in processes:
        proc.terminate()

    # Wait for all threads to finish
    for _, thread in processes:
        thread.join()

    print("All iperf3 servers have been terminated.")
