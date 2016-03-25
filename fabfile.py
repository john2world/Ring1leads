from fabric.api import env
from fabric.operations import local
from fabric.utils import puts
from fabric.context_managers import hide
from fabric.contrib.console import confirm
from fabric import colors

from StringIO import StringIO
from distutils.version import StrictVersion
from rl_proto2 import settings

import fabutils

import sys
import shutil
import os.path


env.git_repo = 'https://git.heroku.com/ringlead-dqp-001.git'
env.abort_exception = fabutils.FabricException


def pull():
    """ Pull from master
    """
    if not fabutils.check_virtualenv():
        if not confirm(
                'It seems you are running outside a virtualenv. '
                'Would you like to proceed anyway?'):
            fabutils.error('Ok, aborting.')
            sys.exit(1)

        puts('')

    # pull
    fabutils.try_local(
        'git pull origin master', 'Pulling from origin',
        'Unable to pull, aborting.', abort=True)

    puts('')

    fabutils.try_local(
        'git pull heroku master', 'Pulling from heroku',
        'Unable to pull, aborting.', abort=True)

    puts('')

    uninstalled_programs = []

    # check if kyoto-cabinet is installed
    fabutils.check_program_exists(
        'kyoto-cabinet', 'kchashmgr --version', result=uninstalled_programs)

    # print uninstalled programs
    if uninstalled_programs:
        uninstalled_programs = ', '.join(uninstalled_programs)

        puts('Aborting... It seems you don\'t have some '
             'required programs: {}'.format(uninstalled_programs))

        sys.exit(1)

    puts('')

    # install requirements
    fabutils.try_local(
        'pip install -r requirements.txt',
        'Installing requirements',
        'An error occurred when running requirements.', abort=True)

    puts('')

    # run migrations
    fabutils.try_local(
        'python manage.py migrate',
        'Running migrations',
        'Unable to run migrations.', abort=True)

    puts('')

    # fetch tags
    fabutils.try_local(
        'git fetch --tags',
        'Fetching tags',
        'Unable to fetch tags. Proceeding anyway...', capture=True)

    fabutils.puts('Current version: {}'.format(colors.green(_get_version())))


def setup_local():
    """ Setup local environment
    """
    pull()
    puts('')

    # setup heroku repo
    output = fabutils.try_local(
        'git remote', 'Checking remotes', capture=True, abort=True)

    remotes = output.splitlines()

    puts('Checking heroku remote for git: ', end='')

    if 'heroku' not in remotes:
        with hide('running', 'stdout', 'stderr'):
            local('git remote add heroku {}'.format(env.git_repo))
        fabutils.ok('created')
    else:
        fabutils.ok('already exists')

    # cp local_settings
    fabutils.puts_flush('Checking local_settings.py: ', end='')

    local_settings = os.path.join(
        os.path.dirname(__file__), 'rl_proto2', 'local_settings.py')

    if not os.path.exists(local_settings):
        fabutils.ok('copied')
        shutil.copyfile(local_settings + '.sample', local_settings)
    else:
        fabutils.ok('already exists')

    puts('')

    # run tests
    _run_tests()


def push(skiptests=True, branch='master'):
    """ Push to master
    """
    if not skiptests:
        if not _run_tests():
            puts('Cannot proceed. Tests are failing.')
            return

        puts('')

    # pipefail: the return value of a pipeline is the status of the last
    # command to exit with a non-zero status, or zero if no command exited with
    # a non-zero status
    result = fabutils.try_local(
        'set -o pipefail; git diff {branch}..origin | flake8 --diff'.format(
            branch=branch),
        label='Checking for errors/warnings')

    if not result:
        if not confirm(
                'There are some errors/warnings in the commits you are about '
                'to push.\nDo you want to proceed anyway?'):
            sys.exit(1)

        puts('')

    fabutils.try_local('git push origin {branch}'.format(branch=branch),
                       label='Pushing to master')


def version():
    version = _get_version()

    if not version:
        fabutils.error(
            'Unable to detect the current version using: git tag -l')
        return

    puts('Current version is: {}'.format(version))
    puts('Next version is: {}'.format(fabutils.inc_version(version)))


def deploy(skiptests=False):
    """ Deploy to production
    """

    # pull from heroku
    fabutils.try_local(
        'git pull heroku master', 'Pulling from Heroku',
        'Unable to pull from heroku remote. Aborting.', abort=True)

    puts('')

    # determine the current version (used to rollback if needed)
    current_version = _get_version()
    next_version = fabutils.inc_version(current_version)

    # run tests
    if not skiptests:
        if not _run_tests():
            puts('Cannot proceed. Tests are failing')
            return

        puts('')

    # pause celery and wait for tasks to finish
    fabutils.puts_sep('Pause celery and wait for tasks to finish ',
                      char=colors.cyan('>'))

    buf = StringIO()
    proc = fabutils.heroku_run(
        'python manage.py runscript celery_stop_consuming', buf)

    if proc.returncode > 0 or 'No (valid) module for script' in buf.read():
        fabutils.puts_sep(
            suffix=colors.red(' error'), size=(79 - 6), char=colors.cyan('<'))
        fabutils.error('Cannot proceed with the deploy')
        return
    else:
        fabutils.puts_sep(
            suffix=colors.green(' ok'), size=(79 - 3), char=colors.cyan('<'))

    puts('')

    # enter maintenance mode
    fabutils.try_local(
        'heroku maintenance:on', 'Entering maintenance mode',
        'Unable to enter maintenance mode. Aborting.', abort=True)

    puts('')

    # push to heroku
    fabutils.try_local(
        'git push heroku master -f', 'Pushing to Heroku',
        'Aborting: Unable to push to Heroku. The maintenance mode will '
        'remain. You can disable it by running: '
        'heroku maintenance:off', abort=True)

    puts('')

    # deploy
    deployed = _deploy()

    if deployed:
        # leave maintenance mode
        fabutils.try_local(
            'heroku maintenance:off', 'Leaving maintenance mode',
            'Unable to leave maintenance mode. Please do it manually.')

        puts('')

        # tag this build
        if fabutils.try_local(
                'git tag {}'.format(next_version), 'Registering tag',
                'Unable to register tag. Please do it manually.'):
            with hide('running', 'stdout'):
                local('git push --tags')

        puts('')

        # update remote version
        fabutils.try_local(
                'heroku config:set APP_VERSION={}'.format(settings.APP_VERSION),
                'Updating remote APP_VERSION',
                'Unable to update APP_VERSION. Please do it manually.')

        puts('')

        fabutils.ok('Deploy tag: {}'.format(next_version))

    else:
        puts('')

        fabutils.error('Deploy failed.')
        fabutils.error('The last good tag is: {}'.format(current_version))


def run_tests():
    _run_tests()


def _deploy():
    # run migrations
    if fabutils.heroku_run('python manage.py migrate').returncode > 0:
        return False

    return True


def _run_tests():
    return fabutils.try_local(
        'python manage.py test --failfast', 'Running tests')


def _get_version():
    with hide('running', 'stdout', 'stderr'):
        local('git fetch --tags', capture=True)
        tags = local('git tag -l', capture=True).splitlines()
        tags.sort(key=StrictVersion)
        if tags:
            return tags[-1]
