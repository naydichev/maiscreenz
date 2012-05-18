""" This is the base file for maiscreenz, it only contains the version number and the sample config generator. """

import os.path, ConfigParser

__version__ = '0.1'
__config__  = os.path.expanduser('~/.maiscreenzrc')

def write_sample_config():
    """ Write out a sample configuration file for the user to edit.
    This will give some basis for the allowed fields. """

    if existing_config(__config__):
        print 'Configuration file already exists (%s)!' % __config__
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
    config.set('local_settings', 'watch_path', os.path.expanduser('~/Desktop'))

    with open( __config__, 'wb' ) as conffile:
        config.write( conffile )

    print 'Sample configuration file (%s) written. Please edit it before running.' % __config__

def existing_config(config_path):
    """ Check for the existence of config file. """
    if not os.path.exists(config_path):
        return False
    return True
