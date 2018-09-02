# QEMU Monitor Protocol Python class
#
# Copyright (C) 2009 Red Hat Inc.
#
# This work is licensed under the terms of the GNU GPL, version 2.  See
# the COPYING file in the top-level directory.

import socket, json, time
from optparse import OptionParser


class QMPError(Exception):
    pass


class QMPConnectError(QMPError):
    pass


class QEMUMonitorProtocol:
    def connect(self):
        print(self.filename)
        self.sock.connect(self.filename)
        data = self.__json_read()
        if data is None:
            raise QMPConnectError
        if not 'QMP' in data:
            raise QMPConnectError
        return data['QMP']['capabilities']

    def close(self):
        self.sock.close()

    def send_raw(self, line):
        self.sock.send(str(line))
        return self.__json_read()

    def send(self, cmdline, timeout=30, convert=True):
        end_time = time.time() + timeout
        if convert:
            cmd = self.__build_cmd(cmdline)
        else:
            cmd = cmdline
            print("*cmdline = %s" % cmd)
        print(cmd)
        self.__json_send(cmd)
        while time.time() < end_time:
            resp = self.__json_read()
            if resp is None:
                return (False, None)
            elif resp.has_key('error'):
                return (False, resp['error'])
            elif resp.has_key('return'):
                return (True, resp['return'])

    def read(self, timeout=30):
        o = ""
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                o += self.sock.recv(1024)
                if len(o) > 0:
                    break
            except:
                time.sleep(0.01)
        if len(o) > 0:
            return json.loads(o)
        else:
            return None

    def __build_cmd(self, cmdline):
        cmdargs = cmdline.split()
        qmpcmd = {'execute': cmdargs[0], 'arguments': {}}
        for arg in cmdargs[1:]:
            opt = arg.split('=')
            try:
                value = int(opt[1])
            except ValueError:
                value = opt[1]
            qmpcmd['arguments'][opt[0]] = value
            print("*cmdline = %s" % cmdline)
        return qmpcmd

    def __json_send(self, cmd):
        # XXX: We have to send any additional char, otherwise
        # the Server won't read our input
        self.sock.send(json.dumps(cmd) + ' ')

    def __json_read(self):
        try:
            return json.loads(self.sock.recv(1024).decode())
        except ValueError:
            return

    def __init__(self, host, port, protocol="tcp"):
        if protocol == "tcp":
            self.filename = (host, int(port))
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif protocol == "unix":
            self.filename = filename
            print(self.filename)
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # self.sock.setblocking(0)
        self.sock.settimeout(5)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('-n', '--num', dest='num', default='10', help='Times want to try')
    parser.add_option('-f', '--file', dest='port', default='4444', help='QMP port/filename')
    parser.add_option('-p', '--protocol', dest='protocol', default='tcp', help='QMP protocol')


    def usage():
        parser.print_help()
        sys.exit(1)


    options, args = parser.parse_args()

    print(options)
    if len(args) > 0:
        usage()

    num = int(options.num)
    qmp_filename = options.port
    qmp_protocol = options.protocol
    qmp_socket = QEMUMonitorProtocol("cn30", qmp_filename, qmp_protocol)
    qmp_socket.connect()
    qmp_socket.send("qmp_capabilities")
    qmp_socket.close()

##########################################################
# Usage
# Options:
#  -h, --help            show this help message and exit
#  -n NUM, --num=NUM     Times want to try
#  -f PORT, --file=PORT  QMP port/filename
#  -p PROTOCOL, --protocol=PROTOCOL
#                        QMP protocol
# e.g: # python xxxxx.py -n $NUM -f $PORT
##########################################################
