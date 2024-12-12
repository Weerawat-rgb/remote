import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
from app import app  # นำเข้า Flask app จากไฟล์ app.py
import logging
logging.basicConfig(
    filename='C:\\RemoteManage\\flask_service.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class FlaskService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FlaskWebService"  # ชื่อ service
    _svc_display_name_ = "Flask Web Service"  # ชื่อที่แสดงใน Services
    _svc_description_ = "Flask Web Application Service"  # คำอธิบาย service

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.is_alive = False

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        try:
            logging.info('Starting Flask app...')
            app.run(host='0.0.0.0', port=8080)
        except Exception as e:
            logging.error(f'Error starting Flask app: {str(e)}')
            raise

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(FlaskService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(FlaskService)
