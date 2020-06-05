import subprocess

def get_cpu_load_line():
    cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
    out = subprocess.check_output(cmd, shell=True)
    return out.decode('utf-8')

def get_cpu_temp_line():
    cmd = "cat /sys/class/thermal/thermal_zone0/temp | awk '{printf \"CPU temp: %3.1fc\", $1/1000}'"
    out = subprocess.check_output(cmd, shell=True)
    return out.decode('utf-8')

def get_mem_line():
    cmd = "free -m | awk 'NR==2{printf \"RAM:  %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
    out = subprocess.check_output(cmd, shell=True)
    return out.decode('utf-8')

def get_disk_line():
    cmd = "df -h | awk '$NF==\"/\"{printf \"Card: %d/%dGB %s\", $3,$2,$5}'"
    out = subprocess.check_output(cmd, shell=True)
    return out.decode('utf-8')

def get_disk_line():
    cmd = "df -h | awk '$NF==\"/\"{printf \"disk: %d/%dGB %s\", $3,$2,$5}'"
    out = subprocess.check_output(cmd, shell=True)
    return out.decode('utf-8')

def get_ip_lines():
    cmd = 'ip -4 -br addr'
    out = subprocess.check_output(cmd, shell=True)
    return out.decode('utf-8').split('\n')

def get_saved_connections():
    cmd = 'nmcli -t c show'
    out = subprocess.check_output(cmd, shell=True)
    out = out.decode('utf-8')
    lines = out.split('\n')

    parsed = []
    for line in lines:
        if not line:
            continue

        line = line.replace(r'\:', '-')
        line = line.replace(r'\\', '-')
        fields = line.split(':')
        name, uuid, _, dev = fields
        d = {}
        d['name'] = name
        d['uuid'] = uuid
        d['up'] = 1 if dev else 0
        parsed.append(d)

    return parsed
