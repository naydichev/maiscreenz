""" The grunt work of the maiscreenz tool.
    Watch the watchPath and upload it to hostname, etc., etc.
"""

import ConfigParser
import hashlib
import os
import sys
import socket

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
        self.config_file = os.path.expanduser('~/.maiscreenzrc')
        self.settings    = {}

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

    def write_sample_config(self):
        """ Write out a sample configuration file for the user to edit.
        This will give some basis for the allowed fields. """

        if self.existing_config(self.config_file):
            print 'Configuration file already exists (%s)!' % self.config_file
            return


        config = ConfigParser.ConfigParser()

        config.add_section('maiscreenz')
        config.set('maiscreenz', 'sample_data', 'true')

        config.add_section('remote_settings')
        config.set('remote_settings', 'hostname', 'my.di.af')
        config.set('remote_settings', 'username', 'diaf')
        config.set('remote_settings', 'scp_path', 'html/')
        config.set('remote_settings', 'web_path', '/')
        config.set('remote_settings', 'protocol', 'http://')

        config.add_section('local_settings')
        config.set('local_settings', 'file_match', 'Screen Shot')
        config.set('local_settings', 'delete_after_upload', 'true')
        config.set('local_settings', 'use_growl', 'true')
        config.set('local_settings', 'watch_path', \
                os.path.expanduser('~/Desktop'))

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

        self.settings['local']['growl'].notify(
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

            if not self.upload_file(filename, self.get_remote_path(newname)):
                self.growl(
                        'Error uploading: %s' % sys.exc_info()[1].message,
                        'Failure'
                        )
                return

            web_url = self.get_web_url(newname)
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

    def upload_file(self, local_file, remote_file):
        """ Upload the local_file to the remote_file location. """
        client = paramiko.SSHClient()

        try:
            client.load_system_host_keys()
        except IOError as err:
            sys.stderr.write(str(err))
            return False

        try:
            client.connect(
                    self.settings['remote']['hostname'],
                    username=self.settings['remote']['username']
                    )
        except (BadHostKeyException, AuthenticationException,
                SSHException, socket.error) as err:
            sys.stderr.write(str(err))
            return False

        sftp = client.open_sftp()
        sftp.put(local_file, remote_file)
        sftp.close()
        client.close()

        return True

    def register_growl(self):
        """ Registers with growl for notifications, only if enabled. """
        growl = gntp.notifier.GrowlNotifier(
                applicationName = "maiscreenz",
                notifications = [ "Upload Complete", "Failure" ],
                defaultNotifications = [ "Upload Complete" ],
                )
        growl.register()
        self.settings['local']['growl'] = growl

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
