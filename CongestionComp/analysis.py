import pyshark
from collections import defaultdict
import matplotlib.pyplot as plt
from tqdm import tqdm

def analyze_pcap(pcap_file, congestion_scheme):
    cap = pyshark.FileCapture(pcap_file, display_filter='tcp')

    total_bytes_sent = 0
    useful_bytes = 0 
    total_packets = 0
    packet_loss_count = 0
    window_sizes = []
    time_stamps = []
    byte_counts = defaultdict(float)
    sequence_numbers = defaultdict(set)

    for pkt in tqdm(cap, desc="Processing packets"):
        try:
            if 'TCP' in pkt and hasattr(pkt.tcp, 'len'):
                total_packets += 1
                timestamp = float(pkt.sniff_timestamp)
                time_stamps.append(timestamp)
                bytes_sent = int(pkt.tcp.len)
                total_bytes_sent += bytes_sent

                flow_key = (
                    pkt.ip.src,
                    pkt.tcp.srcport,
                    pkt.ip.dst,
                    pkt.tcp.dstport
                )

                seq_num = int(pkt.tcp.seq)
                if seq_num not in sequence_numbers[flow_key]:
                    sequence_numbers[flow_key].add(seq_num)
                    useful_bytes += bytes_sent

                if hasattr(pkt.tcp, 'flags') and 'R' in pkt.tcp.flags:
                    packet_loss_count += 1
                
                if hasattr(pkt.tcp, 'window_size'):
                    window_sizes.append(int(pkt.tcp.window_size))

                time_slot = int(timestamp)
                byte_counts[time_slot] += bytes_sent

        except AttributeError:
            continue

    cap.close()

    if not time_stamps:
        print(f"No valid packets found in {pcap_file}. Skipping analysis.")
        return {
            'Throughput (Mbps)': 0,
            'Goodput (Mbps)': 0,
            'Packet Loss Rate (%)': 0,
            'Max Window Size (bytes)': 0
        }

    duration = max(time_stamps) - min(time_stamps)
    if duration <= 0:
        duration = 1

    throughput = (total_bytes_sent * 8) / (duration * 1000000)

    goodput = (useful_bytes * 8) / (duration * 1000000)

    packet_loss_rate = (packet_loss_count / total_packets) * 100 if total_packets > 0 else 0

    max_window_size = max(window_sizes) if window_sizes else 0

    times = sorted(byte_counts.keys())
    throughput_over_time = [byte_counts[t] * 8 / 1000000 for t in times]
    plt.figure(figsize=(10, 6))
    plt.plot(times, throughput_over_time, label=f'Throughput ({congestion_scheme})')
    plt.xlabel('Time (s)')
    plt.ylabel('Throughput (Mbps)')
    plt.title(f'Throughput Over Time - {congestion_scheme}')
    plt.legend()
    plt.grid()
    plt.savefig(f'throughput_{congestion_scheme}.png')
    plt.close()

    if window_sizes:
        plt.figure(figsize=(10, 6))
        plt.plot(time_stamps[:len(window_sizes)], window_sizes, label=f'Window Size ({congestion_scheme})')
        plt.xlabel('Time (s)')
        plt.ylabel('Window Size (bytes)')
        plt.title(f'Max Window Size Over Time - {congestion_scheme}')
        plt.legend()
        plt.grid()
        plt.savefig(f'window_size_{congestion_scheme}.png')
        plt.close()

    results = {
        'Throughput (Mbps)': throughput,
        'Goodput (Mbps)': goodput,
        'Packet Loss Rate (%)': packet_loss_rate,
        'Max Window Size (bytes)': max_window_size
    }
    return results

def main():
    congestion_schemes = ['cubic']
    pcap_files = [
        '../PCAPs/Task1/a_cubic_sample.pcap',
    ]

    for scheme, pcap_file in zip(congestion_schemes, pcap_files):
        print(f"\nAnalyzing PCAP file: {pcap_file} (Congestion Scheme: {scheme})")
        results = analyze_pcap(pcap_file, scheme)
        for metric, value in results.items():
            print(f"{metric}: {value:.2f}")

if __name__ == "__main__":
    main()