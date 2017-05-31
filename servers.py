import yaml
import json
import monitor
SERVERS_FILE = "/etc/sesti/servers.yaml"
REPORT_FILES  = "./reports/{}"

def load_yaml(filename):
    try:
        return yaml.load(open(filename).read())
    except:
        return None

class ShortReport:
    def __init__(self, value, measure, text):
        
        self.value = value
        
        self.measure = measure
        if measure == "%" or measure == "C":
            if self.value <= 50:
                self.cls = "bg-success"
            if self.value > 50:
                self.cls = "bg-warning"
            if self.value > 75:
                self.cls = "bg-danger"
        else:
            self.cls = ""

        self.text = text
import pretty
from datetime import datetime

class Server:
    def __init__(self, name, address):
        self.name = name
        self.address = address

        try:
            addr = REPORT_FILES.format(self.address)
            self.report = json.load(open(addr))
            self.error = self.report.get("error",None)
            dt = datetime.strptime(self.report["date"], '%Y-%m-%d %H:%M')
            self.report_date = self.report["date"] + " ({})".format(pretty.date(dt))

            if self.error:
                self.uptime = self.error+": "+self.report.get("description")
                self.headers = []		
            else:
                self.uptime = self.report["uptime"]["text"]
                self.headers = [r.keys()[0] for r in monitor.short_reports]
        except:
            import sys
            print sys.exc_info()
            self.report = None
            self.uptime = "No report for this server yet"
            self.report_date = "Unknown"
            self.headers = []
        
        self.short_reports = []

        for header in self.headers:
            try:
                report_json = self.report["short_reports"][header]
                short_report = ShortReport(report_json["value"], report_json["measure"], report_json["text"])
                self.short_reports.append(short_report)
            except:
                self.short_reports.append(ShortReport(100,"%","No report for data [{}]".format(header)))

def substitute_hash(string, numb):
    return string[:string.index("#")] + str(numb) + string[string.index("#")+2:]

def expand_server_range(rname, data):
    servs = {}
    rng = data["servers"][rname]["range"]
    for i in range(rng[0],rng[1]):
        new_name = substitute_hash(rname, i)
        new_addr = substitute_hash(data["servers"][rname]["address"], i)
        servs[new_name]=Server(new_name, new_addr)
    return servs


def get_servers_and_groups():
    data = load_yaml(SERVERS_FILE)
    servers = {}
    if data.get("servers", None):
        for s in data["servers"]:
            if "#" in s:
                servers.update(expand_server_range(s,data))
            else:
                servers.update({s:Server(s, data["servers"][s]["address"])})
    else:
        return None

    
    for g in data["groups"]:
        ranges = {}
        for s in data["groups"][g]:
            if "#" in s:
                ranges[s] = []
                rng = data["servers"][s]["range"]
                for i in range(rng[0],rng[1]):
                    ranges[s].append(substitute_hash(s, i))

        for k in ranges:
            ind = data["groups"][g].index(k)
            
            data["groups"][g] = data["groups"][g][:ind] + ranges[k] + data["groups"][g][ind+1:]
    return servers, data["groups"]


def group(servers):
    if not servers:
        return {}
    by_groups = {}
    for s in servers:
        v = by_groups.get(s.group, [] )
        v.append(s)
        by_groups[s.group] = v
    return by_groups

if __name__ == "__main__":
    print get_servers_and_groups()
