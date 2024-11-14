"""Functions used by the config classes."""

import os
import shutil


def filter_and_validate(config, validator):
    """Filter and validate the configuration file."""
    default_keys = list(config['DEFAULT'])
    config = {sec_name: {key: config[sec_name][key] for key in config[sec_name]
                         if sec_name == 'DEFAULT' or key not in default_keys} # noqa
              for sec_name in config}
    # Validate the config
    return validator.validate(config)


def write_config(file_name, sections):
    """Write the configuration file."""
    try:
        with open(file_name, 'w', encoding='utf-8') as fp:
            print('# BEE Configuration File', file=fp)
            for sec_name, section in sections.items():
                if not section:
                    continue
                print(file=fp)
                print(f'[{sec_name}]', file=fp)
                for opt_name, value in section.items():
                    print(f'{opt_name} = {value}', file=fp)
    except FileNotFoundError:
        print('Configuration file does not exist!')


def backup(fname):
    """Backup the configuration file."""
    i = 1
    backup_path = f'{fname}.{i}'
    while os.path.exists(backup_path):
        i += 1
        backup_path = f'{fname}.{i}'
    shutil.copy(fname, backup_path)
    print(f'Saved old config to "{backup_path}".')
    print()
