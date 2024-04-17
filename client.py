import subprocess
import threading
import time

ip_server = "192.168.0.28"
bandwidth = 25
n_clients = 20


def generate_iperf_commands(num_commands, ip_server, start_port=5200, bandwidth=25):
    base_command = "stdbuf -oL -eL iperf3 -c {} --reverse -t 60 -p {} -b {}m"
    commands = [base_command.format(ip_server, port, bandwidth) for port in range(start_port, start_port + num_commands)]
    print(commands)
    return commands


def manage_process_output(proce, id):
    while True:
        line = proce.stdout.readline()
        if not line:
            break  # No more output
        print(line)


processes = []
commands = generate_iperf_commands(n_clients, ip_server, bandwidth=bandwidth)

for i, cmd in enumerate(commands):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    thread = threading.Thread(target=manage_process_output, args=(proc, i))
    thread.start()
    processes.append((proc, thread))

try:
    print("iperf3 servers are running in the background...")
    time.sleep(65)
finally:
    for proc, _ in processes:
        proc.terminate()

    for _, thread in processes:
        thread.join()

    print("All iperf3 servers have been terminated.")
