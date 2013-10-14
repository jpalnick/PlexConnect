"""
PlexConnectService

Creates/manages a service for PlexConnect on windows using activePython.
Based on the code found at 
http://code.activestate.com/recipes/576451-how-to-create-a-windows-service-in-python/
http://essiene.blogspot.com/2005/04/python-windows-services.html

 Usage : python PlexConnect_service.py install
 Usage : python PlexConnect_service.py start
 Usage : python PlexConnect_service.py stop
 Usage : python PlexConnect_service.py remove
 
 C:\>python PlexConnect_service.py  --username <username> --password <PASSWORD> --startup auto install

"""

import win32service
import win32serviceutil
import win32api
import win32con
import win32event
import win32evtlogutil
import os

from PlexConnect import startup, shutdown, run, cmdShutdown


class PlexConnectService(win32serviceutil.ServiceFramework):
   
   _svc_name_ = "PlexConnectSrv"
   _svc_display_name_ = "PlexConnect service"
   _svc_description_ = "runs the PlexConnect script"
         
   def __init__(self, args):
           win32serviceutil.ServiceFramework.__init__(self, args)
           self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)           

   def SvcStop(self):
           self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
           win32event.SetEvent(self.hWaitStop)                    
         
   def SvcDoRun(self):
      import servicemanager      
      servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,servicemanager.PYS_SERVICE_STARTED,(self._svc_name_, '')) 
      
      startup()
      
      self.timeout = 3000

      while 1:
         # Wait for service stop signal, if I timeout, loop again
         rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
         # Check to see if self.hWaitStop happened
         if rc == win32event.WAIT_OBJECT_0:
            # Stop signal encountered
            cmdShutdown()
            shutdown()
            servicemanager.LogInfoMsg("%s - STOPPED"%self._svc_display_name_)
            break
         else:
            servicemanager.LogInfoMsg("%s - is alive and well"%self._svc_display_name_)   
               
      
def ctrlHandler(ctrlType):
   return True
                  
if __name__ == '__main__':   
   win32api.SetConsoleCtrlHandler(ctrlHandler, True)   
   win32serviceutil.HandleCommandLine(PlexConnectService)
