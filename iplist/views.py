from django.http import HttpResponse
from django.shortcuts import render
from netmiko import ConnectHandler
from django.http import JsonResponse
import ping3
import socket
import ipaddress
import concurrent.futures
# Create your views here.

def index(request):
    deviceList = []
    with open("ketqua.txt", "r") as f:
        ipList = f.read().split("\n")

    for ip in ipList:
        if ip:
            hostname = ip.split("Hostname:")[1].strip()
            ip_address = ip.split(" ")[1].lstrip("IP:").strip()
            R = {
                "ip": ip_address,
                "hostname": hostname,
                "device_type": "None",
                "username": "None",
                "status": "None",
            }
            deviceList.append(R)
            
    return render(request, "index.html", {'result': deviceList})

def scan_ip(ip_address):
    result = None
    try:
        host = socket.gethostbyaddr(str(ip_address))
        ip = ip_address.ljust(25)
        hostname = host[0].ljust(25)
        result = f"IP: {ip} Hostname: {hostname}"
        print(result)
    except socket.herror:
        pass

    return result


def scan_ip_range(start_ip, end_ip):
    start = ipaddress.IPv4Address(start_ip)
    end = ipaddress.IPv4Address(end_ip)

    ip_range = []
    current_ip = start

    while current_ip <= end:
        ip_range.append(str(current_ip))
        current_ip += 1

    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_ip = {executor.submit(scan_ip, ip): ip for ip in ip_range}
        for future in concurrent.futures.as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Error occurred for IP: {ip}, {e}")

    return results

def scan(request):
    start_ip = request.GET.get('start_ip', '192.168.0.1')
    end_ip = request.GET.get('end_ip', '192.168.0.1')
    results = scan_ip_range(start_ip, end_ip)
    deviceList = []
    for ip in results:
        hostname = ip.split("Hostname:")[1].strip()
        ip_address = ip.split(" ")[1].lstrip("IP:").strip()
        R = {
            "ip": ip_address,
            "hostname": hostname,
            "device_type": "None",
            "username": "None",
            "status": "None",
        }
        deviceList.append(R)
    with open('ketqua.txt', 'w') as file:
        for result in results:
            file.write(result + '\n')
    return JsonResponse({'result': deviceList})

def check_device_status(ip_address):
    try:
        # Kiểm tra trạng thái của thiết bị bằng cách ping

        response = ping3.ping(ip_address, timeout=2)

        # Trả về True nếu ping thành công (thiết bị online)
        if response is None or response is False:
            return False
        else:
            return True

    except ping3.errors.PingError:

        # Thiết bị offline nếu có lỗi xảy ra khi ping
        return False


def check(request):
    deviceList = []
    if request.method == "GET":
        ip_address = request.GET.get("ip", "")
        hostname = request.GET.get("hostname", "")  # Lấy hostname từ tham số truy vấn
        if check_device_status(ip_address):
            status = 'Online'
        else:
            status = 'Offline'
        result = {
            "ip": ip_address,
            "hostname": hostname,
            "device_type": "None",
            "username": "None",
            "status": status,
        }
        deviceList.append(result)
    return JsonResponse({'result': deviceList})

