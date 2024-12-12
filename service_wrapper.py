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
    _svc_name_ = "FlaskWebService1"
    _svc_display_name_ = "Flask Web Service1"
    _svc_description_ = "Flask Web Application Service1"

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
            logging.info('Service is starting...')
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            
            # เพิ่ม debug information
            logging.info(f'Current working directory: {os.getcwd()}')
            logging.info(f'Python path: {sys.path}')
            
            self.main()
        except Exception as e:
            logging.error(f'Service error: {str(e)}', exc_info=True)
            servicemanager.LogErrorMsg(f'Service error: {str(e)}')
            raise

    def main(self):
        try:
            logging.info('Starting Flask app...')
            # แทนที่จะรัน app โดยตรง ให้รันใน thread แยก
            from threading import Thread
            server = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8080})
            server.daemon = True
            server.start()
            
            # รอจนกว่าจะมีการส่งสัญญาณหยุด
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        except Exception as e:
            logging.error(f'Error in main: {str(e)}', exc_info=True)
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