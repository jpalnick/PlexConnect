#!/usr/bin/env python

"""
PlexConnect

Sources:
inter-process-communication (queue): http://pymotw.com/2/multiprocessing/communication.html
"""


import sys, time
from os import sep
import socket
from multiprocessing import Process, Pipe
import signal, errno

import DNSServer, WebServer
import Settings
from Debug import *  # dprint()

class PlexConnect(object):
    
    def __init__(self, logger=dprint):
        signal.signal(signal.SIGINT, self.sighandler_shutdown)
        signal.signal(signal.SIGTERM, self.sighandler_shutdown)
        
        self.logger = logger
    
        self.logger('PlexConnect', 0, "***")
        self.logger('PlexConnect', 0, "PlexConnect")
        self.logger('PlexConnect', 0, "Press CTRL-C to shut down.")
        self.logger('PlexConnect', 0, "***")
    
        self.procs = {}
        self.pipes = {}
        self.param = {}
        self.running = False
        
        success = self.startup()
    
        if success:
            self.run()
        
            self.shutdown()

    def getIP_self(self):
        cfg = self.param['CSettings']
        if cfg.getSetting('enable_plexconnect_autodetect')=='True':
            # get public ip of machine running PlexConnect
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('1.2.3.4', 1000))
            IP = s.getsockname()[0]
            self.logger('PlexConnect', 0, "IP_self: "+IP)
        else:
            # manual override from "settings.cfg"
            IP = cfg.getSetting('ip_plexconnect')
            self.logger('PlexConnect', 0, "IP_self (from settings): "+IP)
    
        return IP


    def startup(self):
        # Settings
        cfg = Settings.CSettings()
        self.param['CSettings'] = cfg
    
        # Logfile
        if cfg.getSetting('logpath').startswith('.'):
            # relative to current path
            logpath = sys.path[0] + sep + cfg.getSetting('logpath')
        else:
            # absolute path
            logpath = cfg.getSetting('logpath')
    
        self.param['LogFile'] = logpath + sep + 'PlexConnect.log'
        self.param['LogLevel'] = cfg.getSetting('loglevel')
        self.logger('PlexConnect', self.param, True)  # init logging, new file, main process
    
        # more Settings
        self.param['IP_self'] = self.getIP_self()
        self.param['HostToIntercept'] = 'trailers.apple.com'
        self.param['HostOfPlexConnect'] = 'atv.plexconnect'
    
        self.running = True
    
        # init DNSServer
        if cfg.getSetting('enable_dnsserver')=='True':
            master, slave = Pipe()  # endpoint [0]-PlexConnect, [1]-DNSServer
            proc = Process(target=DNSServer.Run, args=(slave, self.param))
            proc.start()
        
            time.sleep(0.1)
            if proc.is_alive():
                self.procs['DNSServer'] = proc
                self.pipes['DNSServer'] = master
            else:
                self.logger('PlexConnect', 0, "DNSServer not alive. Shutting down.")
                self.running = False
    
        # init WebServer
        if self.running:
            master, slave = Pipe()  # endpoint [0]-PlexConnect, [1]-WebServer
            proc = Process(target=WebServer.Run, args=(slave, self.param))
            proc.start()
        
            time.sleep(0.1)
            if proc.is_alive():
                self.procs['WebServer'] = proc
                self.pipes['WebServer'] = master
            else:
                self.logger('PlexConnect', 0, "WebServer not alive. Shutting down.")
                self.running = False
    
        # init WebServer_SSL
        if self.running and \
           cfg.getSetting('enable_webserver_ssl')=='True':
            master, slave = Pipe()  # endpoint [0]-PlexConnect, [1]-WebServer
            proc = Process(target=WebServer.Run_SSL, args=(slave, self.param))
            proc.start()
        
            time.sleep(0.1)
            if proc.is_alive():
                self.procs['WebServer_SSL'] = proc
                self.pipes['WebServer_SSL'] = master
            else:
                self.logger('PlexConnect', 0, "WebServer_SSL not alive. Shutting down.")
                self.running = False
    
        # not started successful - clean up
        if not self.running:
            self.cmdShutdown()
            self.shutdown()
    
        return self.running

    def run(self):
        while self.running:
            # do something important
            try:
                time.sleep(60)
            except IOError as e:
                if e.errno == errno.EINTR and not self.running:
                    pass  # mask "IOError: [Errno 4] Interrupted function call"
                else:
                    raise

    def shutdown(self):
        for slave in self.procs:
            self.procs[slave].join()
        self.logger('PlexConnect', 0, "shutdown")

    def cmdShutdown(self):
        self.unning = False
        # send shutdown to all pipes
        for slave in self.pipes:
            self.pipes[slave].send('shutdown')
        self.logger('PlexConnect', 0, "Shutting down.")



    def sighandler_shutdown(self, signum, frame):
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # we heard you!
        self.cmdShutdown()



if __name__=="__main__":
    signal.signal(signal.SIGINT, sighandler_shutdown)
    signal.signal(signal.SIGTERM, sighandler_shutdown)
    
    dprint('PlexConnect', 0, "***")
    dprint('PlexConnect', 0, "PlexConnect")
    dprint('PlexConnect', 0, "Press CTRL-C to shut down.")
    dprint('PlexConnect', 0, "***")
    
    success = startup()
    
    if success:
        run()
        
        shutdown()
