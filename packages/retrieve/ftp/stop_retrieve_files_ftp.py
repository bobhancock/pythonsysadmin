# Send a shutdown request to the server
import pdb
import sys
import os
import socket
from optparse import OptionParser
import retrieval_conf


def main():
    """ main process """

    usage = 'python stop_retrieve_files_ftp.py config_file <host>'
    try:
        parser = OptionParser(usage)
        [options, args] = parser.parse_args()

        if len(args) > 1:
            server_host = args[1]
        else:
            server_host = 'localhost'
            
        config_file = args[0]
    except Exception as e:
        print e
        return 1

    app_conf = retrieval_conf.Appconf(config_file)
    serverPort = int(app_conf.appconf['server_port'])

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((server_host, serverPort))
        sock.sendall(app_conf.appconf['server_shutdown_string'])
        sock.shutdown(1)
        sock.close()
    except socket.Error as e:
        msg='Connection refused: sever may not be running'
        print >>sys.stderr, msg
        return(1)

    # Destroy pid file
    pidfile = app_conf.appconf['daemon_pid']
    if os.path.isfile(pidfile):
        os.remove(pidfile)

    return(0)
if __name__ == "__main__":
    # call main process and exit with its return code
    sys.exit(main())