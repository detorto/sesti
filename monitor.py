from apscheduler.schedulers.blocking import BlockingScheduler
import servers  
import logging
logging.basicConfig()
logger = logging.getLogger()
import paramiko
import json

def get_type(ssh):
    _,stdout,stderr = ssh.exec_command("uname -p");
    arch = stdout.read().strip()

    #udpate core_count
    _,stdout,stderr = ssh.exec_command("nproc")
    cores_count = stdout.read().strip()

    #udpate freq
    _,stdout,stderr = ssh.exec_command("grep \"model name\" /proc/cpuinfo | tail -n 1")
    freq = stdout.read().split()[-1].strip()
    return {"value":"", "measure":"", "text":arch+"\n{} cores".format(cores_count)+"\n{}".format(freq)}


def get_temp(ssh):
    def get_max_core_temp(data):
        max_temp = max([float(line.split()[2][:-3]) for line in filter(None, data.split("\n"))])
        return max_temp
    _, stdout, stderr = ssh.exec_command("sensors | grep Core")
    
    temp = get_max_core_temp(stdout.read())
    
    return {"value":temp, "measure":"C", "text":"{}C".format(temp)}


def get_total_ram(ssh):
    _, stdout, stderr = ssh.exec_command("free -m")
    lines = stdout.read().split("\n");
    ram_total = int(lines[1].split()[1])/1024.0
    return {"value":ram_total, "measure":"Gb", "text":"{0:.6}Gb".format(ram_total)}    


def get_used_ram(ssh):
    _, stdout, stderr = ssh.exec_command("free -m")
    lines = stdout.read().split("\n");
    
    ram_total = int(lines[1].split()[1])/1024.0
    ram_used = int(lines[1].split()[2])/1024.0
    ram_cached = int(lines[1].split()[6])/1024.0

    used_percens = (ram_used-ram_cached)/ram_total * 100.0
   
    text = "U[{0:.4f}Gb]".format(ram_used) + "\n"
    text += "C[{0:.4f}Gb]".format(ram_cached) + "\n"
    text += ": {0:.2f}%".format(used_percens)
    return {"value":used_percens, "measure":"%", "text":text}
    
def get_total_swap(ssh):
    _, stdout, stderr = ssh.exec_command("free -m")
    lines = stdout.read().split("\n");
    swap_total = int(lines[3].split()[1])/1024.0
    swap_used = int(lines[3].split()[2])/1024.0
    return {"value":swap_total, "measure":"Gb", "text":"{0:.4f}Gb".format(swap_total)}

def get_used_swap(ssh):
    _, stdout, stderr = ssh.exec_command("free -m")
    lines = stdout.read().split("\n");
    swap_total = int(lines[3].split()[1])/1024.0
    swap_used = int(lines[3].split()[2])/1024.0

    used_percens = (swap_used)/swap_total * 100.0

    text = "U[{0:.4f}Gb]\n: {1:.2f}%".format(swap_used, used_percens)
    return {"value":used_percens, "measure":"%", "text":text}

def get_home(ssh):
    
    _, stdout, stderr = ssh.exec_command("df /home/ -B M")
    lines = stdout.read().split("\n");
    mounted_on = lines[1].split()[0]
    available = int(lines[1].split()[1][:-1])/1024.0
    used = int(lines[1].split()[2][:-1])/1024.0
    free = int(lines[1].split()[3][:-1])/1024.0
    percentage = int(lines[1].split()[4][:-1])
    
    text = "T[{0:.4f}Gb]\nF[{1:.4f}Gb]".format(available,free)
    return {"value":available, "measure":"Gb", "text":text }


def get_used_home(ssh):
    _, stdout, stderr = ssh.exec_command("df /home/ -B M")
    lines = stdout.read().split("\n");
    mounted_on = lines[1].split()[0]
    
    available = int(lines[1].split()[1][:-1])/1024.0
    used = int(lines[1].split()[2][:-1])/1024.0
    

    free = int(lines[1].split()[3][:-1])/1024.0
    percentage = float(lines[1].split()[4][:-1])
    text = "U[{0:.4f}Gb]\n: {1:.2f}%".format(used,percentage)
    return {"value":percentage, "measure":"%", "text":text}

def get_load(ssh):
    _, stdout, stderr = ssh.exec_command("cat <(grep 'cpu ' /proc/stat) <(sleep 1 && grep 'cpu ' /proc/stat) | awk -v RS=\"\" '{print ($13-$2+$15-$4)*100/($13-$2+$15-$4+$16-$5) \"%\"}'")
    data = stdout.read()
    percentage = float(data.strip()[:-1])
    text = "{:.2f}%".format(percentage)
    return {"value":percentage, "measure":"%", "text":text}    

def get_processes(ssh):
    _, stdout, stderr = ssh.exec_command("top -bn1")
    lines = stdout.read().split("\n");
    user_map = {}
    for l in lines[7:-1]:

        user = l.split()[1]
        if user == "root":
            continue

        v = user_map.get(user,0)
        v+=1
        user_map[user] = v

    items = sorted(user_map.items(), key=lambda x: x[1], reverse= True)[:4 ]
    text = "\n".join(["{}-{}".format(k,v) for k,v in items])
    return {"value":"", "measure":"", "text":text}    

def get_uptime(ssh):
    _, stdout, stderr = ssh.exec_command("uptime")
    uptime = stdout.read().strip().split();
    address = ssh._addr
    
    text = uptime[0]+"\n"
    text += " ".join(uptime[1:5])+"\n"
    text += " ".join(uptime[5:7])+"\n"
    text += " ".join(uptime[9:12])+"\n"
    return {"value":"", "measure":"", "text":text}    


short_reports = \
        [
         {"Type": get_type},
         {"TCore": get_temp},
         {"Load": get_load},
         {"Total RAM": get_total_ram},
         {"Used RAM": get_used_ram},
         {"Total SWAP": get_total_swap},
         {"Used SWAP": get_used_swap},
         {"Total HOME": get_home},
         {"Used HOME": get_used_home},
         {"Processes": get_processes}
         ]

def connect(address):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(address, timeout=10)
	ssh.get_transport().window_size = 3 * 1024 * 1024
        print "do connect"
        ssh._addr = address
        return ssh

def gen_report(server):
    import datetime
    now = datetime.datetime.now()


    try:
        ssh = connect(server.address)
    except Exception as e:
        data = {"error":"connection error","description":str(e), "date":now.strftime("%Y-%m-%d %H:%M")}
        f = open("./reports/{}".format(server.address),"w")
        f.write(json.dumps(data))
	print "Can't connect to {}".format(server.address) 
	return  

    report = {"short_reports":{},"date":now.strftime("%Y-%m-%d %H:%M")}
    uptime = get_uptime(ssh)
    report["uptime"] = uptime
    print "Connected to {}".format(server.address)    
    for op in short_reports:
        try:
            opname = op.keys()[0]
            opfunc = op[opname]
            report["short_reports"][opname] = opfunc(ssh)
        except Exception as e:
            report["short_reports"][opname]="Error: {}".format(str(e))

    f = open("./reports/{}".format(server.address),"w")
    f.write(json.dumps(report))
    ssh.close()

if __name__ == "__main__":
    from multiprocessing.pool import ThreadPool
    import sys, traceback
    def monitor():
        try:
             p = ThreadPool(16)
             servers_,_ = servers.get_servers_and_groups();
             p.map(gen_report,servers_.values())
             p.close()
             p.join()
        except:
             print sys.exc_info()
             traceback.print_exc()
  
	
    sched = BlockingScheduler()
    sched.add_job(monitor, 'interval', replace_existing=True, seconds=30)
    sched.print_jobs()
    sched.start()
