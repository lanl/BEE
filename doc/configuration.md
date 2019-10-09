BeeConfig Module Guide
======================
The BeeConfig class is implemented in beeflow/common/config/config_driver.py. It is a very simple wrapper around the [ConfigParser class](https://docs.python.org/3/library/configparser.html#configparser.ConfigParser) in the [configparser module](https://docs.python.org/3/library/configparser.html) which is part of the python standard library.

Configuration file locations
----------------------------
The BeeConfig class looks for configuration files in two standard locations depending on your platform:

* Linux
   * system configuration file: `/etc/beeflow/bee.conf`
   * user configuration file: `${HOME}/.config/beeflow/bee.conf`
* Mac OSX
   * system configuration file: `/Library/Application Support/beeflow/bee.conf`
   * user configuration file: `${HOME}/Library/Application Support/beeflow/bee.conf`
* Windows
   * system configuration file: **NOT IMPLEMENTED** needs to be in WinReg
   * user configuration file: `%APPDATA%\beeflow\bee.conf`

Configuration file format
-------------------------
The standard library configparser module works with [Windows INI](https://docs.python.org/3/library/configparser.html#supported-ini-file-structure) style configuration files. These files are text-based. They are organized into sections, denoted by square-brackets (**[MySection]**). Within each section, configuration values are key-value pairs. An example:

~~~~
[MyConfiguration]
# Comments are indicated using a hash
ConfigKey1 = value1
; Comments can also be indicated using a semi-colon
ConfigKey2 = value2

[AnotherSection]
~~~~

Configuration file use in BEE
-----------------------------
The BeeConfig class will automatically read the appropriate configurations and create two ConfigParser objects, one for the system configuration and one for the user configuration: BeeConfig.sysconfig and BeeConfig.userconfig. For more information on the methods in the ConfigParser class please see the [documentation](https://docs.python.org/3/library/configparser.html#configparser.ConfigParser).

It is highly advised that you read the ConfigParser class documentation so that you understand how various situations, such as the same key appearing in both a [DEFAULTS] section and your [OwnConfig] sections are handled! Ask questions if you do not understand.

The BeeConfig class leaves it to the developer to decide how to interpret the configuration key-value pairs contained in the configuration files. The same key can appear in the same [section] in both the system and user configuration. The developer will decide which is authoritative. Please document in your code and in a configuration file comment how these situations are being handled in your code.

Example use of BeeConfig class
------------------------------
The following small program creates a BeeConfig object, which automatically reads the system and user configuration files on your platform. It will then use ConfigParser methods to output what sections and values are contained in those files. Feel free to use it as a tool to explore how ConfigParser interprets configuration files.

~~~~
#!/usr/bin/env python3

from config_driver import BeeConfig

bc = BeeConfig()

if not bc.sysconfig.defaults():
    print("System configuration is empty")
else:
    print("System configuration defaults " + str(bc.sysconfig.defaults()))

if not bc.userconfig.defaults():
    print("User configuration is empty")
else:
    print("User configuration defaults " + str(bc.userconfig.defaults()))
    print("User configuration sections " + str(bc.userconfig.sections()))
    for i in bc.userconfig.sections():
        print("User configuration section " + str(i) + " options " + str(bc.userconfig.options(i)))
        for j in bc.userconfig.options(i):
            print("User configuration section " + str(i) + " option " + str(j) + " = " + str(bc.userconfig.get(i, j)))
~~~~
