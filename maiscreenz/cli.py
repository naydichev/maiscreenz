""" CLI code for maiscreenz """
import argparse
import sys
import os
from maiscreenz import Maiscreenz

def main():
    """ main method for maiscreenz cli """

    parser = argparse.ArgumentParser(
            description='daemon management for maiscreenz'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
            "--install-config",
            help="install sample config file",
            action="store_true"
    )
    group.add_argument(
            "--run",
            help="runs the daemon in the foreground",
            action="store_true"
    )
    group.add_argument(
            "--install-daemon",
            help="installs the daemon and starts it",
            action="store_true"
    )
    group.add_argument(
            "--uninstall-daemon",
            help="uninstalls the daemon",
            action="store_true"
    )
    group.add_argument(
            "--test-config",
            help="test the config file",
            action="store_true"
    )
    args = parser.parse_args()

    if args.install_config:
        install_config()
    elif args.run:
        run()
    elif args.install_daemon:
        install_daemon()
    elif args.uninstall_daemon:
        uninstall_daemon()
    elif args.test_config:
        test_config()
    else:
        parser.print_help()

def install_config():
    """ write a sample config file """
    maiscreenz = Maiscreenz()
    maiscreenz.write_sample_config()

def run():
    """ runs the actual daemon in the foreground """
    maiscreenz = Maiscreenz()
    maiscreenz.load_config()
    maiscreenz.start_watching()

def get_plist_path():
    plist_path = os.path.expanduser(
            '~/Library/LaunchAgents/com.thatonekid.maiscreenz.plist'
    )
    return plist_path

def install_daemon():
    """ installs the maiscreenz daemon """
    bin_path = os.path.realpath(sys.argv[0])
    plist_path = get_plist_path()
    plist_data = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" \
        "http://www.apple.com/DTDs/PropertyList-1.0.dtd">

<plist version="1.0">
   <dict>
      <key>Label</key>
      <string>com.thatonekid.maiscreenz</string>
      <key>ProgramArguments</key>
      <array>
          <string>%s</string>
          <string>--run</string>
      </array>
      <key>RunAtLoad</key>
      <true />
      <key>KeepAlive</key>
      <true />
   </dict>
</plist>
    """ % bin_path

    # if this does not pass, do not write the daemon
    test_config(False)

    with open(plist_path, 'w') as fhandle:
        fhandle.write(plist_data)

    os.system('launchctl load %s' % plist_path)

def uninstall_daemon():
    """ uninstalls the maiscreenz daemon """

    plist_path = get_plist_path()
    os.system('launchctl unload %s' % plist_path)


def test_config(print_output=True):
    """ test the config file """
    maiscreenz = Maiscreenz()
    result = maiscreenz.validate_config()

    if result and print_output:
        print 'Tests pass!'
    else:
        return result

if __name__ == '__main__':
    main()
