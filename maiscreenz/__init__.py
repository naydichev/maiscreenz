""" The grunt work of the maiscreenz tool.
    Watch the watchPath and upload it to hostname, etc., etc.
"""

import ConfigParser
import hashlib
import os
import sys
import socket
import boto

from fsevents import Stream, Observer
import paramiko
from paramiko import (BadHostKeyException, AuthenticationException,
    SSHException)
import gntp.notifier
import xerox

__version__ = '0.2'

class Maiscreenz:
    """ maiscreenz class that does the grunt work """

    def __init__(self):
        """ Init our maiscreenz variables """
        self.version     = __version__
        self.config_file = os.path.expanduser(os.environ.get('MAISCREENZRC', '~/.maiscreenzrc'))
        self.settings    = {}
        self.growlapi    = None

    def load_config(self):
        """ Load our config file and make sure that the user has updated it
        accordingly.
        """
        config = ConfigParser.ConfigParser()
        config.read(self.config_file)

        # see if this is a sample, if they deleted this part,
        # we can assume they knew what they were doing.
        try:
            if config.getboolean('maiscreenz', 'sample_data'):
                print 'Please update the config file (%s) accordingly.' \
                        % self.config_file, \
                        'Once done, change sample_data to false'
                sys.exit(1)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            pass

        # setup our hashes
        self.settings['remote'] = {}
        self.settings['local']  = { 'growl_registered' : False }
        self.settings['s3']     = {}

        # and now fetch our values, if anything is missing, that's bad
        remote_settings = [
                'hostname',
                'username',
                'scp_path',
                'web_path',
                'protocol',
                ]

        local_settings = [
                'file_match',
                'watch_path',
                ]
        s3_settings = [
                'access_key',
                'secret_key',
                'bucket',
                ]
        s3_bool = [
                'use_s3',
                ]
        bool_settings = [
                'delete_after_upload',
                'use_growl',
                ]
        try:
            for item in remote_settings:
                self.settings['remote'][item] = \
                        config.get('remote_settings', item)

            for item in local_settings:
                self.settings['local'][item] = \
                        config.get('local_settings', item)

            for item in bool_settings:
                self.settings['local'][item] = \
                        config.getboolean('local_settings', item)

            for item in s3_settings:
                self.settings['s3'][item] = \
                        config.get('s3_settings', item)
            self.settings['s3']['use_s3'] = config.getboolean('s3_settings', 'use_s3')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError) as err:
            sys.stderr.write(str(err) + "\n")
            sys.stderr.write(
                    'Please correct the config file (%s) and then rerun' \
                            % self.config_file + "\n"
                    )
            sys.exit(1)

    @classmethod
    def existing_config(cls, config_path):
        """ Check for the existence of config file. """
        if not os.path.exists(config_path):
            return False
        return True

    def validate_config(self):
        """ Tests the entries in the config file """
        self.load_config()

        # test various settings to ensure they're good

        # test local path
        if not os.path.exists(self.settings['local']['watch_path']):
            sys.stderr.write('Watch path does not exist')
            return False

        if not self.settings['s3']['use_s3']:
            return self.test_ssh()
        else:
            return self.test_s3()

        return False

    def test_ssh(self):
        sshclient = paramiko.SSHClient()

        # test loading keys
        try:
            sshclient.load_system_host_keys()
        except IOError as err:
            sys.stderr.write('Could not load ssh keys')
            sys.stderr.write(str(err) + "\n")
            return False

        # test connecting
        try:
            sshclient.connect(
                    self.settings['remote']['hostname'],
                    username=self.settings['remote']['username']
            )
        except (BadHostKeyException, AuthenticationException,
                SSHException, socket.error) as err:
            sys.stderr.write("Could not connect to remote host")
            sys.stderr.write(str(err) + "\n")
            return False

        # test permissions
        command = 'touch ' + self.get_remote_path('.maiscreenztest')
        try:
            (_, _, stderr) = sshclient.exec_command(command)
            data = stderr.read().lower()
            if data.find('permission denied') != -1 or \
               data.find('no such file') != -1:
                sys.stderr.write('Permissions invalid on remote host')
                return False
        except SSHException as err:
            sys.stderr.write('Could not touch sample file.')
            sys.stderr.write(str(err) + "\n")
            return False
        finally:
            stderr.close()

        sshclient.close()

    def test_s3(self):
        s3 = boto.connect_s3(
                self.settings['s3']['access_key'],
                self.settings['s3']['secret_key']
                )

        try:
            bucket = s3.get_bucket(self.settings['s3']['bucket'])
        except boto.exception.S3ResponseError as err:
            try:
                bucket = s3.create_bucket(self.settings['s3']['bucket'])
            except boto.exception.S3ResponseError as err:
                sys.stderr.write(
                        'Could not create bucket {0}: {1}\n'.format(
                            self.settings['s3']['bucket'],
                            str(err)
                        )
                    )
                return False

        key = bucket.new_key('.maiscreenztest')
        value = 'asdfasa4aafa4yayaeasFAW$A$hgasa'
        key.set_contents_from_string(value)
        key.set_acl('public-read')

        try:
            contents = key.get_contents_as_string()
            assert(contents == value);
        except AssertionError as err:
            sys.stderr.write(
                    'Key value garbled: expected "{0}", got "{1}"\n'.format(
                        value,
                        contents
                    )
                )
            return False

        return True

    def write_sample_config(self):
        """ Write out a sample configuration file for the user to edit.
        This will give some basis for the allowed fields. """

        if self.existing_config(self.config_file):
            print 'Configuration file already exists (%s)!' % self.config_file
            return


        config = ConfigParser.ConfigParser()

        config.add_section('maiscreenz')
        config.set('maiscreenz', 'sample_data', 'true')

        username = 'diaf'

        config.add_section('remote_settings')
        config.set('remote_settings', 'hostname', 'my.di.af')
        config.set('remote_settings', 'username', username)
        config.set('remote_settings', 'scp_path', 'html/')
        config.set('remote_settings', 'web_path', '/')
        config.set('remote_settings', 'protocol', 'http://')

        config.add_section('local_settings')
        config.set('local_settings', 'file_match', 'Screen Shot')
        config.set('local_settings', 'delete_after_upload', 'true')
        config.set('local_settings', 'use_growl', 'true')
        config.set('local_settings', 'watch_path', \
                os.path.expanduser('~/Desktop'))

        config.add_section('s3_settings')
        config.set('s3_settings', 'use_s3', 'false')
        config.set('s3_settings', 'access_key')
        config.set('s3_settings', 'secret_key')
        config.set('s3_settings', 'bucket', username + 'screenshots')

        with open( self.config_file, 'wb' ) as conffile:
            config.write( conffile )

        print 'Sample config file (%s) written. Please edit it before running.'\
                % self.config_file

    @classmethod
    def hash_for_file(cls, filename):
        """ Generate a sha256 hexdigest for a file, so that we can give unique
            short names to our uploaded files.
        """

        # this is a dumb way to appease pylint
        sha256 = getattr(hashlib, 'sha256')()
        with open(filename,'rb') as file_handle:
            for chunk in iter(lambda: file_handle.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def growl(self, message, title = 'Upload Complete'):
        """ Send our Growl notifications, register if necessary """
        if not self.settings['local']['use_growl']:
            return

        if not self.settings['local']['growl_registered']:
            self.register_growl()
            self.settings['local']['growl_registered'] = True

        self.growlapi.notify(
            title       = title,
            noteType    = title,
            sticky      = False,
            priority    = 1,
            description = message
        )

    def capture_event(self, event):
        """ Capture our system events, and perform actions 
            based on what they are.
        """
        # event masks:
        # 2   => update
        # 64  => move_from
        # 128 => move_to
        # 256 => create
        # 512 => delete

        filename = str(event.name)
        fileextension = os.path.splitext(event.name)[1]

        if event.mask in [128, 256] \
            and self.settings['local']['file_match'] in filename \
            and os.path.basename(filename)[0] is not '.':
            hash_str = self.hash_for_file(filename)
            newname = hash_str[0:6] + fileextension

            web_url = ""
            if not self.settings['s3']['use_s3']:
                web_url = self.upload_file(filename, newname)
                if web_url == None:
                    self.growl(
                            'Error uploading: %s' % sys.exc_info()[1].message,
                            'Failure'
                            )
                    return
            else:
                web_url = self.copy_to_s3(filename, newname)

            xerox.copy(web_url)

            self.growl("%s uploaded to %s" % (filename, web_url))

            if self.settings['local']['delete_after_upload']:
                os.remove(filename)

    def get_web_url(self, filename):
        """ Generate the 'web url' based on the new filename. """
        result = ''
        for piece in [ 'protocol', 'hostname', 'web_path' ]:
            result = result + self.settings['remote'][piece]

        return result + filename

    def get_remote_path(self, filename):
        """ Generate the remote path for the new file. """
        return self.settings['remote']['scp_path'] + filename

    def upload_file(self, local_file, remote_filename):
        """ Upload the local_file to the remote_file location. """
        client = paramiko.SSHClient()

        try:
            client.load_system_host_keys()
        except IOError as err:
            sys.stderr.write(str(err))
            return None

        try:
            client.connect(
                    self.settings['remote']['hostname'],
                    username=self.settings['remote']['username']
                    )
        except (BadHostKeyException, AuthenticationException,
                SSHException, socket.error) as err:
            sys.stderr.write(str(err))
            return None

        sftp = client.open_sftp()
        sftp.put(local_file, self.get_remote_path(remote_filename))
        sftp.close()
        client.close()

        return self.get_web_url(remote_filename)

    def copy_to_s3(self, local_filename, newname):
        """ Copies the local_file to s3 and returns the URL """
        s3 = boto.connect_s3(
                self.settings['s3']['access_key'],
                self.settings['s3']['secret_key']
            )
        try:
            bucket = s3.get_bucket(self.settings['s3']['bucket'])
        except boto.exception.S3ResponseError as err:
            sys.stderr.write(
                    'Could not access bucket {0}: {1}\n'.format(
                        self.settings['s3']['bucket'],
                        str(err)
                    )
                )
            return None

        key = bucket.new_key(newname)
        key.set_contents_from_filename(local_filename)
        key.set_acl('public-read')


        return 'https://s3-' + bucket.get_location() + '.amazonaws.com/' + bucket.name + '/' + key.name

    def register_growl(self):
        """ Registers with growl for notifications, only if enabled. """
        growl = gntp.notifier.GrowlNotifier(
                applicationName = "maiscreenz",
                notifications = [ "Upload Complete", "Failure" ],
                defaultNotifications = [ "Upload Complete" ],
                )
        growl.register()
        self.growlapi = growl

    def start_watching(self):
        """ Start watching our paths, and do the main work. """
        # setup
        observer = Observer()
        stream = Stream(
                self.capture_event,
                self.settings['local']['watch_path'],
                file_events=True
                )
        observer.schedule(stream)

        # go go go
        observer.run()
