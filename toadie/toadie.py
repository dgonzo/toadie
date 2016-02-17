__author__ = "David 'Gonzo' Gonzalez"
__email__ = "gonzo@ziff.io"
__copyright__ = "Copyright (C) 2016 David Gonzalez"
__license__ = "Apache License 2.0"
__version__ = "0.1.0"


import click
from .lib.dependencies import Tools
import logging
import os
import errno
import re
import subprocess
import sys
import pkg_resources


log = logging.getLogger()
log.setLevel(logging.DEBUG)

tools = Tools()

def please_update(urls):
    for url in urls:
        click.echo('Please install {} available at: {}'.format(url[0], url[1]))

@click.group()
def main():
    pass


@click.command()
@click.option('--cloud', default='aws',
              help='Check to see if `aws` or `openstack` credentials are properly configured.')
def checkSystem(cloud):
    """Check availability of required tools for developing and deploying on CLOUD.

    \b
    Required:
        - docker
        - docker-compose
        - docker-machine
        - conda or virtualenv

    """
    tool_statuses = tools.check_tools()

    for tool, info in tool_statuses.items():
        if info['version'] == None:
            click.secho(
                '{} is not installed. Install instructions: {}'.format(
                    tool, info['install_url']), fg='red')
        elif info['version_passes'] == False:
            click.secho(
                '{} version [{}] is outdated. Install update: {}'.format(
                    tool, info['version'], info['install_url']), fg='red')
        else:
            click.secho(
                '{} version [{}]: {}'.format(
                    tool, info['version'], 'OK'), fg='green')


@click.command()
@click.option('--cloud', default='aws',
              help='Cloud can be either `aws` or `openstack`.')
def readySystem(cloud):
    """Installs required development tools.

    If required tools are are missing they are installed and required
    configuration files are prepared. System is prepared to use `aws`
    cloud by default with `ecs` (Elastic Container Service). User can
    also use `openstack` with `kubernetes`.
    """
    click.echo('Readying System: {}'.format(cloud))


@click.command()
@click.argument('project_name')
def createProject(project_name):
    """Create a new PROJECT_NAME directory.

    Create a new project directory and dev environment called PROJECT_NAME.
    """
    # Create PROJECT_NAME dir.
    if project_name == ".":
        project_dir = os.path.split(os.getcwd())[-1]
        log.debug("Project name from parent directory: {}".format(
            project_dir))
    else:
        project_dir = project_name
    try:
        os.mkdir(project_dir)
    except OSError as e:
        if e.errno == errno.EEXIST:
            msg = """
            ERROR: {}!
            Cannot create PROJECT_NAME: `{project_dir}`.
            Try a different name or move/delete `{project_dir}`.
            """.format(e.strerror, project_dir=project_dir)
            click.secho(msg, fg='red')
            sys.exit()
        else:
            raise
#    # Create project README.md
#    with open(os.path.join(project_dir,'README.md'), 'w') as f:
#        f.write("# {}".format(project_name.upper().replace('_',' ')))
#    # Create conda env
#    tool_name = re.sub(r'\s','-',project_name)
#    click.echo(
#        "Creating conda env {} python=3.5".format(tool_name))
#    subprocess.getoutput(
#        'conda create --name {}'.format(tool_name))
#    subprocess.getoutput(
#        'conda env export > {}/environment.yml'.format(project_dir))
#    # Create docker-machine project-name
#    click.echo(
#        "Creating docker-machine env {}. May take a minute.".format(
#            tool_name))
#    subprocess.getoutput(
#        'docker-machine create --driver virtualbox {}'.format(tool_name))
#    # Create dotenv file
#    with open(os.path.join(project_dir,'.env'), 'w') as f:
#        f.write('DEBUG=true')
#        f.write('EOF')
#    # Copy scripts

    pkg_scripts = [
        'build-tag-push.py'
    ]
    project_scripts = os.path.join(project_dir,'bin')
    os.mkdir(project_scripts)
    resource_package = __name__
    for script in pkg_scripts:
        resource_path = os.path.join('templates', script)
        template = pkg_resources.resource_string(
            resource_package, resource_path)
        with open(
            os.path.join(project_scripts,script), 'wb'
        ) as f:
                f.write(template)
    # Create Procfile
    click.secho("The following commands have been added to `Procfile`:")
    commands = [
        'up: docker-machine up -d',
        'down: docker-machine stop',
        'clean: docker-machine rm',
        'build: docker-machine build',
        'build-tag-push: python build-tag-push.py'
    ]
    with open(os.path.join(project_dir,'Procfile'), 'w') as f:
        for cmd in commands:
            f.write(cmd)
            cmds = re.match(r'^(.*): (.*)', cmd)
            click.secho(
                """\nshell: {}\nexecute with: honcho start {}""".format(
                    cmds.group(2),
                    cmds.group(1),
                ), fg='blue')


@click.command()
def generateService():
    """Generate service scaffold in services directory."""
    pass


@click.command()
def generateTask():
    """Generate task scaffold in tasks directory."""
    pass


@click.command()
def build_tag_push():
    """Build, Tag, & Push all services to your docker registry."""
    pass

# main.add_command(readySystem, name='ready-system')
main.add_command(checkSystem, name='check-system')
main.add_command(createProject, name='create-project')
main.add_command(generateService, name='generate-service')
main.add_command(generateTask, name='generate-task')
main.add_command(build_tag_push, name='build-tag-push')
