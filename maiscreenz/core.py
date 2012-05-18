""" The grunt work of the maiscreenz tool. Watch the watchPath and upload it to hostname, etc., etc. """

from fsevents import Stream, Observer
import sys, os, hashlib, paramiko, xerox, gntp.notifier, ConfigParser
from maiscreenz import __config__

__settings__ = {}

def load_config():
    """ Load our config file and make sure that the user has updated it accordingly. """
    config = ConfigParser.ConfigParser()
    config.read(__config__)

    # see if this is a sample, if they deleted this part, we can assume they knew what they were doing.
    try:
        if config.getboolean('maiscreenz', 'sample_data'):
            print 'Please update the config file (%s) and update the settings accordingly.  Once done, change sample_data to false' % __config__
            sys.exit(1)
    except ConfigParser.NoSectionError, ConfigParser.NoOptionError:
        pass

    # setup our hashes
    __settings__['remote'] = {}
    __settings__['local']  = { 'growl_registered' : False }

    # and now fetch our values, if anything is missing, that's bad
    try:
        for el in [ 'hostname', 'username', 'scp_path', 'web_path', 'protocol' ]:
            __settings__['remote'][el] = config.get('remote_settings', el)

        for el in [ 'file_match', 'watch_path' ]:
            __settings__['local'][el] = config.get('local_settings', el)

        for el in [ 'delete_after_upload', 'use_growl' ]:
            __settings__['local'][el] = config.getboolean('local_settings', el)
    except ConfigParser.NoSectionError as err:
        sys.stderr.write( str(err) + "\n" )
        sys.stderr.write( 'Please correct the config file (%s) and then rerun' % __config__ + "\n" )
        sys.exit(1)
    except ConfigParser.NoOptionError as err:
        # sys.stderr.write( str(err) + "\n" )
        sys.stderr.write( 'Please correct the config file (%s) and then rerun' % __config__ + "\n" )
        sys.exit(1)

    print __settings__
    sys.exit(0)

def hash_for_file(f):
    """ Generate a sha256 hexdigest for a file, so that we can give unique short names to our uploaded files. """
    hash = hashlib.sha256()
    with open(f,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
         hash.update(chunk)
    return hash.hexdigest()

def growl(message, title = 'Upload Complete'):
    """ Send our Growl notifications, register if necessary """
    if not __settings__['local']['use_growl']:
        return

    if not __settings__['local']['growl_registered']:
        register_growl()
        __settings__['local']['growl_registered'] = True

    growl.notify(
        title       = title,
        noteType    = title,
        sticky      = False,
        priority    = 1,
        description = message
    )

def capture_event(event):
    """ Capture our system events, and perform actions based on what they are. """
    # event masks:
    # 2   => update
    # 64  => move_from
    # 128 => move_to
    # 256 => create
    # 512 => delete

    fileName = str(event.name)
    fileExtension = os.path.splitext(event.name)[1]

    if event.mask in [128, 256] and file_str in fileName:
        hash_str = hash_for_file(fileName)
        newName = hash_str[0:6] + fileExtension

        try:
            upload_file(fileName, get_remote_path(newName))
        except:
            growl('Error uploading: %s' % sys.exc_info()[1].message, 'Failure')
            return

        web_url = get_web_url(newName)
        xerox.copy(web_url)

        growl("%s uploaded to %s" % (fileName, web_url))

        if __settings__['local']['delete_after_upload']:
            os.remove(fileName)

def get_web_url(fileName):
    """ Generate the 'web url' based on the new filename. """
    result = ''
    for piece in [ 'protocol', 'hostname', 'web_path' ]:
        result = result + __settings__['remote'][piece]

    return result + fileName

def get_remote_path(fileName):
    """ Generate the remote path for the new file. """
    return __settings__['remote']['scp_path'] + fileName

def upload_file(local_file, remote_file):
    """ Upload the local_file to the remote_file location. """
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(__settings__['remote']['hostname'], username=__settings__['remote']['username'])
    sftp = client.open_sftp()
    ret = sftp.put(local_file, remote_file)
    sftp.close()
    client.close()

def register_growl():
    """ Registers with growl for notifications, only if enabled. """
    growl = gntp.notifier.GrowlNotifier(
            applicationName = "maiscreenz",
            notifications = [ "Upload Complete", "Failure" ],
            defaultNotifications = [ "Upload Complete" ],
            )
    growl.register()
    __settings__['local']['growl'] = growl

def start_watching():
    """ Start watching our paths, and do the main work. """
    load_config()
    # setup
    observer = Observer()
    stream = Stream(capture_event, __settings__['local']['watch_path'], file_events=True)
    observer.schedule(stream)

    # go go go
    observer.run()
