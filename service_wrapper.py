# service_wrapper.py
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
from pathlib import Path


# แก้ไข path ให้ตรงกับที่ติดตั้งจริง
APP_PATH = r"D:\_myapp\remote"  
PYTHON_PATH = r"C:\Users\weera\AppData\Local\Programs\Python\Python313\python.exe"
LOG_PATH = r"D:\_myapp\remote\logs"

class FlaskService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FlaskWebService"
    _svc_display_name_ = "Flask Web Application Service"
    _svc_description_ = "Windows Service for Flask Web Application"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.process is not None:
            os.kill(self.process.pid, 0)

    def SvcDoRun(self):
        try:
            os.chdir(APP_PATH)
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            
            # สร้างโฟลเดอร์ log ถ้ายังไม่มี
            Path(LOG_PATH).mkdir(parents=True, exist_ok=True)
            
            # เริ่มต้น Flask app
            from subprocess import Popen
            cmd = [PYTHON_PATH, "app.py"]
            self.process = Popen(cmd)
            
            # รอจนกว่าจะมีการสั่ง stop
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
            
        except Exception as e:
            servicemanager.LogErrorMsg(f"Error: {str(e)}")
            os._exit(1)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(FlaskService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(FlaskService)