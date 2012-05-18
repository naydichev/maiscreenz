maiscreenz
==========

A simple python script to upload screenshots to your own server

Requirements
------------

These are all installed via the setup process for you.

- [MacFSEvents][0]: for the mac wonderfulness
- [paramiko][1]: for ssh magicsauce
- [xerox][2]: for clipboard amazingness
- [gntp][3]: a protocol for growling at you

Known Bugs
----------

- `CTRL + C` does not work, I've been forced to `CTRL + Z / kill -9 %1` for now
- The above will not be an issue because I will convert this into a launchctl process

Installing
----------

- clone or download this repo
- run `python setup.py install`
- fix up the settings in ~/.maiscreenzrc, making sure to set sample\_data to false
- run `maiscreenz`, it should be in your path.

To-Do
-----

- Convert this into a launchctl script
- Add the option to regenerate the config file
- Listen to my wonderful audience (of no one) for feature suggestions / bugs.

[0]: http://pypi.python.org/pypi/MacFSEvents
[1]: http://www.lag.net/paramiko
[2]: https://github.com/kennethreitz/xerox
[3]: https://github.com/kfdm/gntp/
