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
    # Create project README.md
    with open(os.path.join(project_dir,'README.md'), 'w') as f:
        f.write("# {}\n\n".format(project_name.upper().replace('_',' ')))
    # Create conda env
    tool_name = re.sub(r'\s','-',project_name)
    click.echo(
        "Creating conda env {} python=3.5".format(tool_name))
    subprocess.getoutput(
        'conda create --name {}'.format(tool_name))
    subprocess.getoutput(
        'conda env export > {}/environment.yml'.format(project_dir))
    # Create docker-machine project-name
    click.echo(
        "Creating docker-machine env {}. May take a minute.".format(
            tool_name))
    subprocess.getoutput(
        'docker-machine create --driver virtualbox {}'.format(tool_name))
    # Create dotenv file
    with open(os.path.join(project_dir,'.env'), 'w') as f:
        f.write('DEBUG=true')
        f.write('EOF')
    # Copy scripts

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
    readme = open(os.path.join(project_dir,'README.md'), 'a')
    readme.write("# Available honcho commands:\n\n")
    with open(os.path.join(project_dir,'Procfile'), 'w') as f:
        for cmd in commands:
            f.write(cmd)
            cmds = re.match(r'^(.*): (.*)', cmd)
            click.secho(
                """\nshell: {}\nexecute with: honcho start {}""".format(
                    cmds.group(2),
                    cmds.group(1)
                ), fg='blue')
            readme.write("    # {} execute with:\n    $ honcho start {}\n".format(
                cmds.group(2),
                cmds.group(1)
            ))
    readme.close()
    # Create .env and dotenv.example files
    first_line = "COMMENT=This file was generated by {}".format('toadie')
    with open(os.path.join(project_dir,'.env'), 'w') as f:
        f.write(first_line)
    with open(os.path.join(project_dir,'dotenv.example'), 'w') as f:
        f.write(first_line)
    with open(os.path.join(project_dir, '.gitignore'), 'w') as f:
        f.write("# added by toadie\n.env")


@click.command()
def updateDotenv():
    """Parse environment variables out of project files.

    Parses environment variables out of project (py) files and updates
    `.env` and `dotenv.example` files. Returns missing values in each file.
    """
    log.debug("{}".format(sys._getframe().f_code.co_name))
    # Parse environment variables out of project files.
    if not os.path.isfile('.env'):
        click.secho("No `.env` file found. Make sure you are in your project directory.", fg='red')
        sys.exit()
    project_env_var = re.compile(r'os.environ.get\([\'\"](.*?)[\'\"]')
    for dir_contents in os.walk('.'):
        for filename in dir_contents[2]:
            with open(os.path.join(dir_contents[0],filename), 'r') as f:
                contents = f.read()
                project_env_vars = set(project_env_var.findall(contents))
    # Get set of variables in .env.
    dotenv_var = re.compile(r'^(.*)=')
    with open('.env', 'r') as f:
        contents = f.read()
        dot_env_vars = set(dotenv_var.findall(contents))
    missing_dotenv_vars = project_env_vars - dot_env_vars
    # Add missing to .env
    if len(missing_dotenv_vars) > 0:
        click.echo("The following variables were missing in `.env` and set to '__blank__'.")
    for var in sorted(missing_dotenv_vars):
        with open('.env', 'a') as f:
            f.write("{}=__blank__\n".format(var))
            click.secho("{} set to __blank__. Update before running.".format(var), fg='yellow')
    # Get set of missing varialbes in dotenv.example
    with open('dotenv.example', 'r') as f:
        contents = f.read()
        example_env_vars = set(dotenv_var.findall(contents))
    missing_example_vars = (project_env_vars | dot_env_vars) - example_env_vars
    # Add missing to dotenv.example
    if len(missing_example_vars) > 0:
        click.echo("The following variables were missing in `dotenv.example` and added.")
    for var in sorted(missing_example_vars):
        with open('dotenv.example', 'a') as f:
            f.write("{}=\n".format(var))
            click.secho("{}".format(var), fg='blue')


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
main.add_command(updateDotenv, name='update-dotenv')
