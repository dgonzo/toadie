__author__ = "David 'Gonzo' Gonzalez"
__email__ = "gonzo@ziff.io"
__copyright__ = "Copyright (C) 2016 David Gonzalez"
__license__ = "Apache License 2.0"
__version__ = "0.1.0"


import click
from .lib.dependencies import Tools

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
    """Create a new project directory and dev environment called PROJECT_NAME."""
    # Create project README.rst

    # Create docker-machine project-name

    # Create dotenv file

    # Create Procfile

    click.echo("Created: {}".format(project_name))


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
