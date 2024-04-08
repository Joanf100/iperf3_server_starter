import subprocess
import threading
import time

required_mbps = 20

def generate_iperf_commands(num_commands, start_port=5200):
    base_command = "stdbuf -oL -eL iperf3 -c 192.168.140.47 -P 2 --reverse -t 60 -p {} -b 10000000"
    commands = [base_command.format(port) for port in range(start_port, start_port + num_commands)]
    return commands

def manage_process_output(proce, id):
    while True:
        line = proce.stdout.readline()
        if not line:
            break  # No more output
        print(line)


processes = []
commands = generate_iperf_commands(10)

for i, cmd in enumerate(commands):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    # Start a thread to handle this process's output
    thread = threading.Thread(target=manage_process_output, args=(proc, i))
    thread.start()
    processes.append((proc, thread))

try:
    print("iperf3 servers are running in the background...")
    time.sleep(60)
finally:
    # Ensure all iperf3 servers are terminated
    for proc, _ in processes:
        proc.terminate()

    # Wait for all threads to finish
    for _, thread in processes:
        thread.join()

    print("All iperf3 servers have been terminated.")
