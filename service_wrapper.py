import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import logging
from app import app

class FlaskService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FlaskWebService"
    _svc_display_name_ = "Flask Web Service"
    _svc_description_ = "Flask Web Application Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True

        # ย้ายการตั้งค่า logging มาไว้ใน __init__
        logging.basicConfig(
            filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'service.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
        
        # ย้าย stdout redirect มาไว้ใน __init__
        sys.stdout = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'service_output.log'), 'a', encoding='utf-8')

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.is_alive = False

    def SvcDoRun(self):
        try:
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            self.main()
        except Exception as e:
            logging.error(f'Service error: {str(e)}')
            servicemanager.LogErrorMsg(f'Service error: {str(e)}')

    def main(self):
        try:
            logging.info('Starting Flask app...')
            app.run(host='0.0.0.0', port=8080)
        except Exception as e:
            logging.error(f'Error starting Flask app: {str(e)}')
            raise

if __name__ == '__main__':
    if len(sys.argv) == 1:
        try:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(FlaskService)
            servicemanager.StartServiceCtrlDispatcher()
        except Exception as e:
            logging.error(f'Service dispatcher error: {str(e)}')
            raise
    else:
        win32serviceutil.HandleCommandLine(FlaskService)