import socket,struct
import re

__all__ = ["IPChecker", "PermError"]

def _dottedQuadToNum(ip):
    "convert decimal dotted quad string to long integer"
    return struct.unpack('<L',socket.inet_aton(ip))[0]

def _isValidIp(ip):
    matchObj = re.match(r'([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3}).*', ip)
    if matchObj:
        for i in xrange(1,5):
            n = int(matchObj.group(i))
            
            if n < 0 or n > 255:
                # print "address item", i, "(", n, ") does not fall between 0 and 255 inclusive."
                return False
        # print "address is valid"
        return True
    else:
        # print "address is not valid"
        return False

class IPChecker(object):
    def __init__(self):
        self.nets = []
        self.knownips = []
        
    def add(self, data):
        if type(data) is str:
            if "," in data or ";" in data:
                data_list = re.split('; |, ', data)
                for d in data_list:
                    self.add(d.strip())
            if "/" in data:
                print "data is CIDR"
                netaddr,bits = data.split('/')
                bits = int(bits)
                if _isValidIp(netaddr):
                    # print "CIDR address is valid"
                    if bits >= 0 and bits < 32:
                        # print "CIDR is valid"
                        netmask = _dottedQuadToNum(netaddr) & ((2L<<int(bits)-1) - 1)
                        self.nets.append((netaddr, bits, netmask))
                    elif bits == 32:
                        # print "CIDR is valid but equates to a single ip. adding to known ips."
                        self.knownips.append(netaddr)
                    else:
                        # print "CIDR bits must be an integer between 0 and 32"
                        return
                else:
                    # print "CIDR address is not valid"
                    return
            elif _isValidIp(data.strip()):
                # print "data is single ip"
                self.knownips.append(data.strip())
            else:
                # print "data format can't be identified"
                pass
        elif type(data) is list and all(map(lambda x: type(x) is str, data)):
            # print "got a list of strings. will iterate through the list."
            for d in data:
                self.add(d.strip())
        else:
            print "data is not of type string or a list of strings"
                
    
        
    def addCIDR(self, net):
        netaddr,bits = net.split('/')
        netmask = _dottedQuadToNum(netaddr) & ((2L<<int(bits)-1) - 1)
        self.nets.append((netaddr, bits, netmask))
    
    def clearNets(self):
        self.nets = []
    
    def printNets(self):
        for net in self.nets:
            print net
    
    def addKnownIp(self, ip):
        self.knownips.append(ip)

    def clearKnownIps(self):
        self.knownips = []
        
    def printKnownIps(self):
        for ip in self.knownips:
            print ip

    def printValid(self):
        print "nets:"
        self.printNets()
        print "ips:"
        self.printKnownIps()
    
    def checkIp(self, ip):
        if ip in self.knownips:
            # print "ip", ip, "found in known ip list"
            return True

        # print "ip not found in known ip list. moving on to the networks."

        ipaddr = _dottedQuadToNum(ip)
        for net in self.nets:
            netaddr,bits,netmask = net
            if ipaddr & netmask == netmask:
                # print "found match for", ip, "in", (netaddr, bits)
                return True
        
        # print "no match for", ip, "found"
        return False

class PermError(Exception):
    pass