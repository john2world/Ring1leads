import sys
import pipes
import subprocess
import shlex

from fabric.colors import green, red, cyan
from fabric.operations import local
from fabric.utils import puts
from fabric.context_managers import hide


class FabricException(Exception):
    pass


def ok(message=None, *args, **kwargs):
    puts(green(message or 'ok'), *args, **kwargs)


def error(message=None, *args, **kwargs):
    puts(red(message or 'error'), *args, **kwargs)


def puts_flush(*args, **kwargs):
    puts(*args, **kwargs)
    sys.stdout.flush()


def puts_sep(prefix='', suffix='', size=None, char='-', *args, **kwargs):
    if size is None:
        size = 79 - len(prefix) - len(suffix)
    puts_flush('{}{}{}'.format(prefix, char * size, suffix), *args, **kwargs)


def check_program_exists(program, command, result):
    puts('Checking {}: '.format(program), end='')
    if not executable_exists(command):
        result.append(program)
        error('not found')
    else:
        ok()


def executable_exists(command):
    with hide('running', 'stdout', 'stderr'):
        try:
            local(command, capture=True)
        except FabricException:
            return False
        return True


def try_local(*args, **kwargs):
    capture = kwargs.pop('capture', False)
    abort = kwargs.pop('abort', False)

    if not capture:
        result = _try_local(*args, **kwargs)

        if not result and abort:
            sys.exit(1)

        return result

    result = _try_local_capture(*args, **kwargs)

    if result is None and abort:
        sys.exit(1)

    return result


def _try_local(command, label, error_message=None):
    label += ' '
    puts_sep(prefix=label, size=79 - len(label), char=cyan('>'))

    try:
        puts('{} {}'.format(cyan('Command:'), command))
        puts_sep(char=cyan('-'))

        with hide('aborts', 'running'):
            local(command, capture=False)

    except FabricException:
        puts_sep(suffix=red(' error'), size=79-5, char=cyan('<'))

        if error_message:
            error(error_message)

        return False

    else:
        puts_sep(suffix=green(' ok'), size=79-3, char=cyan('<'))

        return True


def _try_local_capture(command, label, error_message=None):
    puts_flush(label + ': ', end='')

    try:
        with hide('aborts', 'running'):
            output = local(command, capture=True)

    except FabricException:
        # If capture is True, we must return None in case of fail
        # otherwise the captured output
        error(error_message)

    else:
        ok()

        return output


def local_stream(command, buffer=None):
    proc = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)

    for c in iter(lambda: proc.stdout.read(1), ''):
        sys.stdout.write(c)
        if buffer is not None:
            buffer.write(c)

    if buffer:
        buffer.seek(0)

    proc.wait()

    return proc


def heroku_run(command, buffer=None):
    local_command = 'heroku run {} --exit-code'.format(pipes.quote(command))
    return local_stream(local_command, buffer=buffer)


def inc_version(version):
    if not version:
        return '0.0.1'

    version = version.split('.')

    if len(version) == 1:
        version.extend([0, 1])
    elif len(version) == 2:
        version.append(1)
    elif version[-1].isdigit():
        version[-1] = int(version[-1]) + 1

    return '.'.join(map(str, version))


def check_virtualenv():
    # Reference: http://stackoverflow.com/a/1883251/639465
    return hasattr(sys, 'real_prefix')
