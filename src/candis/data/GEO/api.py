# imports - standard imports
import os
import threading

# imports - third-party imports
from ftplib import FTP
from urllib.parse import urlparse

# imports - module imports
from candis.util import assign_if_none

class API():
    DOWNLOADING = 'DOWNLOADING'
    COMPLETE    = 'COMPLETE'
    
    def __init__(self, path='', ftype='suppl'):
        self.ftype = ftype
        self.path = path
        self.fpath = None
        self.thread = None
        self.status = API.DOWNLOADING
        self.logs = [ ]

    def set_status(self, status):
        self.status = status

    def _ftp_connect(self, host, usr=None, pswd=None):
        ftp = FTP(host, usr, pswd) if usr and pswd else FTP(host)
        ftp.login()
        self.ftp = ftp

    def _ftp_close(self):
        if isinstance(self.ftp, FTP):
            self.ftp.quit()
            print("Closed successfully!")
        self.ftp = None

    def raw_data(self, ftp_link, series_accession, path=None):
        self.logs.append('Making a ftp connection')

        tar_file = f'{series_accession}_RAW.tar'
        url = ''.join([ftp_link, 'suppl/', tar_file])
        host = urlparse(url).netloc
        file_name = urlparse(url).path

        self._ftp_connect(host)

        self.logs.append('Checking Path')

        if path:
            if os.path.exists(os.path.abspath(path)):
                self.path = os.path.abspath(path)
            else:
                raise OSError("given path doesn't exists")
        else:
            if(isinstance(self.path, dict)):
                self.path = ''
            self.path = os.path.abspath(self.path)

        file_path = os.path.join(self.path, tar_file)
        self.fpath = file_path

        self.logs.append(f"Downloading {tar_file} at {os.path.abspath(self.path)}")
        with open(file_path, 'wb') as f:
            try:
                self.ftp.retrbinary(f'RETR {file_name}', f.write)
                self.logs.append("Downloaded")
                self.set_status(API.COMPLETE)
            except EOFError:
                print("Connection closed, couldn't download the file.")
            except Exception as e:
                print(f"Error {e}")
            self._ftp_close()

    def download(self, ftp_link, series_accession, path=None):
        self.thread = threading.Thread(target = self.raw_data, args = (ftp_link, series_accession, path))
        self.thread.start()
