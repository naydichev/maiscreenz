""" CLI code for maiscreenz """
from maiscreenz import Maiscreenz
import argparse

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
    args = parser.parse_args()

    if args.install_config:
        install_config()
    elif args.run:
        run()
    elif args.install_daemon:
        install_daemon()
    elif args.uninstall_daemon:
        uninstall_daemon()
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

def install_daemon():
    """ installs the maiscreenz daemon """
    pass

def uninstall_daemon():
    """ uninstalls the maiscreenz daemon """
    pass

if __name__ == '__main__':
    main()
