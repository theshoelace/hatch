import os
import pexpect
import shutil
import signal
import subprocess
from tempfile import TemporaryDirectory

from hatch.settings import load_settings
from hatch.utils import (
    NEED_SUBPROCESS_SHELL, ON_WINDOWS, basepath, temp_move_path
)

DEFAULT_SHELL = 'cmd' if ON_WINDOWS else 'bash'


def get_terminal_dimensions():
    columns, lines = shutil.get_terminal_size()
    return lines, columns


def cmd_shell(exe_dir, shell_path):
    result = subprocess.run(
        [shell_path or 'cmd', '/k', os.path.join(exe_dir, 'activate.bat')],
        shell=NEED_SUBPROCESS_SHELL
    )
    return result.returncode


def ps_shell(exe_dir, shell_path):
    result = subprocess.run(
        [shell_path or 'powershell', '-executionpolicy', 'bypass', '-NoExit',
         '-NoLogo', '-File', os.path.join(exe_dir, 'activate.ps1')],
        shell=NEED_SUBPROCESS_SHELL
    )
    return result.returncode


def bash_shell(exe_dir, shell_path):
    terminal = pexpect.spawn(
        shell_path or 'bash',
        args=['-i'],
        dimensions=get_terminal_dimensions()
    )

    def sigwinch_passthrough(sig, data):
        terminal.setwinsize(*get_terminal_dimensions())
    signal.signal(signal.SIGWINCH, sigwinch_passthrough)

    terminal.sendline('source "{}"'.format(os.path.join(exe_dir, 'activate')))
    terminal.interact(escape_character=None)
    terminal.close()
    return terminal.exitstatus


def fish_shell(exe_dir, shell_path):
    terminal = pexpect.spawn(
        shell_path or 'fish',
        args=['-i'],
        dimensions=get_terminal_dimensions()
    )

    def sigwinch_passthrough(sig, data):
        terminal.setwinsize(*get_terminal_dimensions())
    signal.signal(signal.SIGWINCH, sigwinch_passthrough)

    terminal.sendline('. "{}"'.format(os.path.join(exe_dir, 'activate.fish')))
    terminal.interact(escape_character=None)
    terminal.close()
    return terminal.exitstatus


def zsh_shell(exe_dir, shell_path):
    terminal = pexpect.spawn(
        shell_path or 'zsh',
        args=['-i'],
        dimensions=get_terminal_dimensions()
    )

    def sigwinch_passthrough(sig, data):
        terminal.setwinsize(*get_terminal_dimensions())
    signal.signal(signal.SIGWINCH, sigwinch_passthrough)

    terminal.sendline('source "{}"'.format(os.path.join(exe_dir, 'activate')))
    terminal.interact(escape_character=None)
    terminal.close()
    return terminal.exitstatus


def xonsh_shell(exe_dir, shell_path):
    with TemporaryDirectory() as d:
        with temp_move_path(os.path.expanduser('~{}.xonshrc'.format(os.path.sep)), d) as path:
            new_config = ''
            if path:
                with open(path, 'r') as f:
                    new_config += f.read()

            env_name = os.path.dirname(exe_dir)
            new_config += (
                '\n$PROMPT_FIELDS["env_name"] = "({env_name})"\n'
                ''.format(env_name=env_name)
            )

            new_config_path = os.path.join(d, 'new.xonshrc')
            with open(new_config_path, 'w') as f:
                f.write(new_config)

            result = subprocess.run(
                [shell_path or 'xonsh', '--rc', new_config_path],
                shell=NEED_SUBPROCESS_SHELL
            )
            return result.returncode


def unknown_shell(shell_name):
    result = subprocess.run(shell_name.split(), shell=NEED_SUBPROCESS_SHELL)
    return result.returncode


SHELL_COMMANDS = {
    'cmd': cmd_shell,
    'powershell': ps_shell,
    'ps': ps_shell,
    'bash': bash_shell,
    'fish': fish_shell,
    'zsh': zsh_shell,
    'xonsh': xonsh_shell,
}


def get_default_shell_info(shell_name=None, settings=None):
    if not shell_name:
        settings = settings or load_settings(lazy=True)

        shell_name = settings.get('shell')
        if shell_name:
            return shell_name, None

        shell_path = os.environ.get('SHELL')
        if shell_path:
            shell_name = basepath(shell_path)
        else:
            shell_name = DEFAULT_SHELL

        return shell_name, shell_path

    return shell_name, None


def run_shell(exe_dir, shell_name=None):
    shell_name, shell_path = get_default_shell_info(shell_name)
    shell = SHELL_COMMANDS.get(shell_name)
    return shell(exe_dir, shell_path) if shell else unknown_shell(shell_name)
