#!/usr/bin/env python

from fsevents import Stream,Observer
import sys, os, hashlib, paramiko, xerox, gntp.notifier

#############
# <configs> #
#############
hostname = 'my.di.af'
protocol = 'http://'
username = 'diaf'
scp_path = 'html/'
web_path = '/'
file_str = 'Screen Shot'
growl    = True
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
def upload(event):
    # moved to a name with Screen Shot in it
    fileName = str(event.name)
    if event.mask is 128 and file_str in fileName:
        # split the extension
        fileExtension = os.path.splitext(event.name)[1]
        hash_str = hash_for_file(fileName)
        newName = hash_str[0:6] + fileExtension
        upload_file(fileName, scp_path + newName)
        web_url = protocol + hostname + web_path + newName
        xerox.copy(web_url)
        if growl:
            growl.notify(
                    title = "Upload Complete",
                    description = "Uploaded %s to %s" % (fileName, web_url),
                    noteType = "Upload Complete",
                    sticky = False,
                    priority = 1,
                    )

def upload_file(local_file, remote_file):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(hostname, username=username)
    sftp = client.open_sftp()
    ret = sftp.put(local_file, remote_file)
    sftp.close()
    client.close()
    return ret

def register_growl():
    growl = gntp.notifier.GrowlNotifier(
            applicationName = "maiscreenz",
            notifications = [ "Upload Complete" ],
            defaultNotifications = [ "Upload Complete" ],
            )
    growl.register()

    return growl

# usage check
if len(sys.argv) < 2:
    print "Must specify a path"
    sys.exit(1)

# setup runtime variables
watchPath = sys.argv[1]

# setup growl
if growl:
    growl = register_growl()

# setup
observer = Observer()
stream = Stream(upload, watchPath, file_events=True)
observer.schedule(stream)

# go go go
observer.run()
