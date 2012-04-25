#!/usr/bin/env python

from fsevents import Stream,Observer
import sys, os, hashlib, paramiko, xerox

#############
# <configs> #
#############
hostname = 'my.di.af'
protocol = 'http://'
username = 'diaf'
scp_path = 'html/'
web_path = '/'
file_str = 'Screen Shot'
##############
# </configs> #
##############

def hash_for_file(f):
    hash = hashlib.sha256()
    with open(f,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
         hash.update(chunk)
    return hash.hexdigest()

# event masks:
# 2   => update
# 64  => move_from
# 128 => move_to
# 256 => create
# 512 => delete
def callback(event):
    # moved to a name with Screen Shot in it
    if event.mask is 128 and file_str in str(event.name):
        # split the extension
        fileExtension = os.path.splitext(event.name)[1]
        newName = str(hash_for_file(event.name))[0:6] + fileExtension
        upload_file(event.name, scp_path + newName)
        xerox.copy(protocol + hostname + web_path + newName)


def upload_file(local_file, remote_file):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(hostname, username=username)
    sftp = client.open_sftp()
    ret = sftp.put(local_file, remote_file)
    sftp.close()
    client.close()
    return ret

if len(sys.argv) < 2:
    print "Must specify a path"
    sys.exit(1)

watchPath = sys.argv[1]

observer = Observer()
stream = Stream(callback, watchPath, file_events=True)
observer.schedule(stream)
observer.run()
ssh_client.close()
