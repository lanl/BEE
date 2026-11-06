"""Functions used by the config classes."""

import os
import shutil

from configparser import ConfigParser

def filter_and_validate(config, validator):
    """Filter and validate the configuration.

    The configuration is normalized in memory (e.g. the scheduler attribute
    sections are added/removed when the workload scheduler changes) and
    validated; the config file itself is never modified here.
    """
    if isinstance(config,dict):
        config_parser = ConfigParser()
        config_parser.read_dict(config)
        config = config_parser

    scheduler = config.get('DEFAULT','workload_scheduler',fallback='Slurm').strip()
    if config.has_section('slurm'):
        use_commands = config.getboolean('slurm','use_commands',fallback=False)
    else:
        use_commands = False

    sections_to_remove = []
    if scheduler == 'Flux':
        sections_to_remove = ['slurm attributes','slurm command attributes']
        if not config.has_section('flux attributes'):
            config.add_section('flux attributes')
        if not config.get('flux attributes','attributes',fallback='').strip():
            config.set('flux attributes','attributes','id,queue,runtime,nodelist')
    elif scheduler == 'Slurm':
        if use_commands:
            sections_to_remove = ['flux attributes','slurm attributes']
            if not config.has_section('slurm command attributes'):
                config.add_section('slurm command attributes')
            if not config.get('slurm command attributes','attributes',fallback='').strip():
                config.set('slurm command attributes','attributes','Partition,RunTime,NodeList')
        else:
            sections_to_remove = ['flux attributes','slurm command attributes']
            if not config.has_section('slurm attributes'):
                config.add_section('slurm attributes')
            if not config.get('slurm attributes','attributes',fallback='').strip():
                config.set('slurm attributes','attributes','partition,nodes')

    for sec in sections_to_remove:
        if config.has_section(sec):
            config.remove_section(sec)

    default_keys = list(config['DEFAULT'])
    config = {sec_name: {key: config[sec_name][key] for key in config[sec_name]
                         if sec_name == 'DEFAULT' or key not in default_keys}
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
                    if isinstance(value, (list, tuple)):
                        value = ",".join(str(v).strip() for v in value if str(v).strip())
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
