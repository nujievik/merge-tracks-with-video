from . import config, locale, sys_argv

def set_initial_flags():
    locale.set_locale()
    config.set_flags_by_config()
    sys_argv.set_flags_by_sys_argv()
