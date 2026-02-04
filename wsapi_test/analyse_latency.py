import csv
import sys
import numpy as np

def read_latency(file_path):
    recv_send_deltas = []
    out_in_deltas = []

    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                recv_delta = int(row["recv_time - send_time (ms)"])
                out_delta = int(row["out_time - in_time (ms)"])
                recv_send_deltas.append(recv_delta)
                out_in_deltas.append(out_delta)
            except Exception:
                continue

    return recv_send_deltas, out_in_deltas

def print_stats(label, data):
    if not data:
        print(f"[{label}] No data found.")
        return

    print(f"\n[{label}]")
    print(f"  AVG: {np.mean(data):.2f} ms")
    print(f"  P95: {np.percentile(data, 95):.2f} ms")
    print(f"  P99: {np.percentile(data, 99):.2f} ms")

def analyze_file(file_path):
    recv_send, out_in = read_latency(file_path)
    print(f"\n分析文件: {file_path}")
    print_stats("recv_time - send_time", recv_send)
    print_stats("out_time - in_time", out_in)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_latency.py order.csv [cancel.csv]")
        sys.exit(1)

    for path in sys.argv[1:]:
        analyze_file(path)
