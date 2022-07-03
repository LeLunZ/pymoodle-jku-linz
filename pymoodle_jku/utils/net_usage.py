import psutil
import time


def net_interfaces():
    return list(psutil.net_io_counters(pernic=True, nowrap=True).keys())


def net_usage(inf="en0"):  # change the inf variable according to the interface
    net_stat = psutil.net_io_counters(pernic=True, nowrap=True)[inf]
    net_in_1 = net_stat.bytes_recv
    net_out_1 = net_stat.bytes_sent
    time.sleep(1)
    net_stat = psutil.net_io_counters(pernic=True, nowrap=True)[inf]
    net_in_2 = net_stat.bytes_recv
    net_out_2 = net_stat.bytes_sent

    net_in = round((net_in_2 - net_in_1) * 8 / 1024 / 1024, 3)
    net_out = round((net_out_2 - net_out_1) * 8 / 1024 / 1024, 3)

    return net_in, net_out
    # print(f"Current net-usage:\nIN: {net_in} Mbit/s, OUT: {net_out} Mbit/s")
