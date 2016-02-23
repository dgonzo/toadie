__author__ = "David 'Gonzo' Gonzalez"
__email__ = "davidbgonzalez@gmail.com"
__copyright__ = "Copyright (C) 2016 David Gonzalez"
__license__ = "Apache License 2.0"
__version__ = "0.1.1a1"


import click
from .lib.dependencies import Tools
from .lib.components import StackComponent
import logging
import os
import errno
import re
import subprocess
import sys
import pkg_resources
import json
import yaml


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

tools = Tools()

RESOURCE_PACKAGE = __name__

def please_update(urls):
    for url in urls:
        click.echo('Please install {} available at: {}'.format(url[0], url[1]))


def create_conda(project_name):
    """Create conda environment if neccessary."""
    # Check system for project tools.
    tool_name = re.sub(r'[\s_]', '-', project_name)

    # Check conda env and create if necessary.
    envs = json.loads(subprocess.getoutput('conda env list --json'))['envs']

    if not [i for i in envs if tool_name in i]:
        click.echo(
            "Creating: conda env {} python=3.5".format(tool_name))
        # Create conda env.
        status = subprocess.getstatusoutput('conda create -n {} python=3.5'.format(tool_name))
        if status[0] == 0:
            click.secho("Conda env `{}` created.".format(tool_name), fg='green')
            click.secho("""Activate with: $ source activate {}
                    """.format(tool_name), fg='yellow')
        else:
            click.secho(status[1], fg='red')
    else:
        click.secho("""Conda environment ready.""".format(tool_name), fg='green')
        click.secho("""Activate with: $ source activate {}
                    """.format(tool_name), fg='yellow')


def create_machine(project_name):
    """Create docker-machine environment and create if neccessary."""
    tool_name = re.sub(r'[\s_]', '-', project_name)
    machines = subprocess.getstatusoutput('docker-machine ls -q')
    machines = machines[1].split('\n')
    msg = """Activate with either:
        $ eval $(docker-machine env {envname})

        or if you have docker-machine bash completion:

        $ docker-machine use {envname}
        """.format(envname=tool_name)

    if not [i for i in machines if tool_name in i]:
        click.echo(
            "Creating: docker-machine env {}".format(tool_name)
        )
        status = subprocess.getstatusoutput(
            'docker-machine create --driver virtualbox {}'.format(tool_name))
        if status[0] == 0:
            click.secho("Docker-machine env `{}` created.".format(tool_name), fg='green')
            click.secho(msg, fg='yellow')
        else:
            click.secho(status[1], fg='red')
    else:
        click.secho("Docker-machine environment ready.", fg='green')
        click.secho(msg, fg='yellow')


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
        - docker-machine
        - docker-compose
        - conda

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
@click.argument('project_path')
@click.option('--cloud', default='aws',
              help='Cloud can be either `aws` or `openstack`.')
def readySystem(project_path, cloud):
    """Installs required development tools."""
    if project_path == ".":
        project_dir = os.getcwd()
        project_name = os.path.split(os.getcwd())[-1]
    else:
        project_dir = os.join.path(os.getcwd(), project_path)
        project_name = project_path

    create_conda(project_name)
    create_machine(project_name)

    if cloud == 'openstack':
        cloud_configs = [
            'OS_VERSION=__blank__',
            'OS_USERNAME=__blank__',
            'OS_PASSWORD=__blank__',
            'OS_PROJECT_ID=__blank__',
            'OS_REGION=__blank__',
            'OS_AUTH_URL=__blank__',
        ]
        with open(os.path.join(project_dir, '.env'), 'a') as _:
            for line in cloud_configs:
                _.write(line+"\n")
    else:
        cloud_configs = [
            'AWS_ACCESS_KEY_ID=__blank__',
            'AWS_SECRET_ACCESS_KEY=__blank__'
        ]
        with open(os.path.join(project_dir, '.env'), 'a') as _:
            for line in cloud_configs:
                _.write(line+"\n")


@click.command()
@click.argument('project_name')
def createProject(project_name):
    """Create a new PROJECT_NAME directory.

        Create a new project directory and dev environment called PROJECT_NAME.
    """

    # Create PROJECT_NAME dir.
    if project_name == ".":
        project_dir = os.path.split(os.getcwd())[-1]
        log.debug("Project name from parent directory: {}".format(project_dir))
    else:
        project_dir = project_name
    try:
        os.mkdir(project_dir)
    except OSError as err:
        if err.errno == errno.EEXIST:
            msg = """
            ERROR: {}!
            Cannot create PROJECT_NAME: `{project_dir}`.
            Try a different name or move/delete `{project_dir}`.
            """.format(err.strerror, project_dir=project_dir)
            click.secho(msg, fg='red')
            sys.exit()
        else:
            raise

    # Check system for project tools.
    create_conda(project_name)
    create_machine(project_name)

   # Create project README.md
    with open(os.path.join(project_dir, 'README.md'), 'w') as _:
        _.write("# {}\n\n".format(project_name.upper().replace('_', ' ')))
    # Check system for project tools.

    # Create docker-compose file
    with open(os.path.join(project_dir, 'docker-compose.yml'), 'w') as _:
        _.write("version: '2.0'\n")

    # Copy scripts
    pkg_scripts = [
        'build-tag-push.py'
    ]
    project_scripts = os.path.join(project_dir, 'bin')
    os.mkdir(project_scripts)
    for script in pkg_scripts:
        resource_path = os.path.join('templates', script)
        template = pkg_resources.resource_string(
            RESOURCE_PACKAGE, resource_path)
        with open(os.path.join(project_scripts, script), 'wb') as _:
            _.write(template)

    # Create Procfile
    click.secho("The following commands have been added to `Procfile`:")
    commands = [
        'up: docker-compose up -d',
        'down: docker-compose stop',
        'clean: docker-compose rm',
        'build: docker-compose build',
    ]
    readme = open(os.path.join(project_dir,'README.md'), 'a')
    readme.write("# Available honcho commands:\n\n")
    cmd_instructions = "\nYou can also load environmental variables found in `.env` before arbitrary commands using: honcho run `cmd`"
    with open(os.path.join(project_dir,'Procfile'), 'w') as _:
        for cmd in commands:
            _.write(cmd+"\n")
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
            readme.write(cmd_instructions)
    readme.close()
    click.echo(cmd_instructions)

    # Create config files .env, dotenv.example, and .gitignore files.
    first_line = "COMMENT=This file was generated by {}\n".format('toadie')

    with open(os.path.join(project_dir, '.env'), 'w') as _:
        _.write(first_line)

    with open(os.path.join(project_dir, 'dotenv.example'), 'w') as _:
        _.write(first_line)

    with open(os.path.join(project_dir, '.gitignore'), 'w') as _:
        _.write("# added by toadie\n.env")


@click.command()
def updateDotenv():
    """Parse environment variables out of project files.

        Parses environment variables out of project (py) files and update
        `.env` and `dotenv.example` files. Returns missing values in each file.
    """

    log.debug("{}".format(sys._getframe().f_code.co_name))
    # Parse environment variables out of project files.
    if not os.path.isfile('.env'):
        click.secho("No `.env` file found. Make sure you are in your project directory.", fg='red')
        sys.exit()
    project_env_var = re.compile(r'os.environ.get\([\'\"](.*?)[\'\"]')
    for dir_contents in os.walk('.'):
        log.debug(dir_contents[2])
        for filename in dir_contents[2]:
            with open(os.path.join(dir_contents[0],filename), 'r') as _:
                contents = _.read()
                project_env_vars = set(project_env_var.findall(contents))
    # Get set of variables in .env.
    dotenv_var = re.compile(r'^(.*)=')
    with open('.env', 'r') as _:
        contents = _.read()
        dot_env_vars = set(dotenv_var.findall(contents))
    missing_dotenv_vars = project_env_vars - dot_env_vars
    # Add missing to .env
    if len(missing_dotenv_vars) > 0:
        click.echo("The following variables were missing in `.env` and set to '__blank__'.")
    for var in sorted(missing_dotenv_vars):
        with open('.env', 'a') as _:
            _.write("{}=__blank__\n".format(var))
            click.secho("{} set to __blank__. Update before running.".format(var), fg='yellow')
    # Get set of missing varialbes in dotenv.example
    with open('dotenv.example', 'r') as _:
        contents = _.read()
        example_env_vars = set(dotenv_var.findall(contents))
    missing_example_vars = (project_env_vars | dot_env_vars) - example_env_vars
    # Add missing to dotenv.example
    if len(missing_example_vars) > 0:
        click.echo("The following variables were missing in `dotenv.example` and added.")
    for var in sorted(missing_example_vars):
        with open('dotenv.example', 'a') as _:
            _.write("{}=\n".format(var))
            click.secho("{}".format(var), fg='blue')


@click.command()
@click.argument("component-name")
@click.option("--force", is_flag=True)
@click.option("--interface",
              default='queue',
              type=click.Choice(['queue','reset','hybrid']))
@click.option("--component-type",
              default='service',
              type=click.Choice(['service','task']))
def generateStackComponent(component_name, force, interface, component_type):

    """Generate stack component scaffold in directory named COMPONENT_NAME.

    \b
    Stack components are of one of three types:
        - services: long-running applications
        - tasks: short-running batch applications

    \b
    Stack components have interfaces:
        - queue: a component that only consumes (dequeues & enqueues) tasks
        - rest: a component that only responds to RESTful http requests
        - hybrid: a component that consumes tasks and responds to http requests

    Queue based components are like distributed daemons. They consume (dequeue) tasks from the task queue and may also produce (enqueue) tasks for additional processing in the stack. Queue based components cannot be reached by http request and as such should be monitored and redeployed when not healthy. Queue inputs and outputs can be declared in:

        \b
        - ./<component_type>/<component-name>/promise.yml

    REST based components can be called ad hoc via http requests. They should be designed to provide ad hoc functionality in the stack that can be accessed via their api by processes external to the stack. REST inputs and outputs can be declared in:

        \b
        - ./<component_type>/<component-name>/raml.yml

    Hybrid components can be called from ad hoc http requests and consume or produce tasks from the task queue. An example use case for a hybrid task would be to provide a RESTful api to post jobs from an external system into the stack i.e. posting a job to a hybrid service via http would result in a new task enqueued to a queue for additional processing by queue based components. Hybrid components' inputs and outputs can be declared in:

        \b
        - REST inputs and outputs: ./<component_type>/<component-name>/raml.yml
        - Queue inputs and outputs: ./<component_type>/<component-name>/promise.yml

    Components not authored in python need only conform to inputs and outputs laid out above and be deployable via a Dockerfile based app.
    """
    project_path = os.getcwd()
    component_dir = os.path.join(project_path, component_type+"s", component_name)

    # Verify component directory doesn't exist.
    if not force:
        if os.path.exists(component_dir):
            click.secho(
                """
                {} named {} already exists. To overwrite rerun with `--force`
                """.format(component_type.capitalize(), component_name), fg='red')
            sys.exit()

    component = StackComponent(
        component_name,
        component_type,
        project_path,
        resource_package=RESOURCE_PACKAGE
    )

    if interface == 'queue':
        component.create_queue_component()
    elif interface == 'rest':
        component.create_rest_component()
    elif interface == 'hybrid':
        component.create_hybrid_component()

    with open(os.path.join(project_path, 'docker-compose.yml'), 'r') as _:
        docker_compose = yaml.load(_)
    services = docker_compose['services'].keys()
    if 'errlogger' not in services:
        errlogger = StackComponent('errlogger', 'service', project_path,
                                   resource_package=RESOURCE_PACKAGE)
        errlogger.create_queue_component()
        click.echo('Created errlogger service.')

    if 'logger' not in services:
        logger = StackComponent('logger', 'service', project_path,
                                resource_package=RESOURCE_PACKAGE)
        logger.create_queue_component()
        click.echo('Created logger service.')

    click.secho("[{}] {} component created: {}".format(interface.upper(),
                                                       component_type.capitalize(),
                                                       component_name), fg='green')


@click.command()
@click.argument('component_rel_path')
def generateMock(component_rel_path):
    """Generates a mock for component found in COMPONENT_REL_PATH."""
    if os.path.split(component_rel_path)[1]:
        fullpath = os.path.join(os.getcwd(), component_rel_path)
    else:
        fullpath = os.path.join(os.getcwd(), os.path.split(component_rel_path)[0])

    try:
        component_name = os.path.split(fullpath)[1]
        component_name = 'mock_for_'+component_name
    except:
        raise

    mock_component = StackComponent(
        component_name,
        component_type='mock',
        project_path=os.getcwd(),
        resource_package=RESOURCE_PACKAGE,
    )

    mock_component.create_mock_component()

    click.secho("Stack component `{}` created".format(component_name), fg='green')
    click.secho("To enable/disable mock use `toggle-mock`", fg='yellow')


@click.command()
@click.argument('mock_rel_path')
def toggleMock(mock_rel_path):
    """Enables/disables mock stack component found in MOCK_REL_PATH."""
    if os.path.split(mock_rel_path)[1]:
        fullpath = os.path.join(os.getcwd(), mock_rel_path)
    else:
        fullpath = os.path.join(os.getcwd(), os.path.split(mock_rel_path)[0])

    try:
        component_path, component_name = os.path.split(fullpath)
    except:
        raise

    if os.path.split(component_path)[1] != 'mocks':
        click.secho("This does not appear to be a `mock` component.", fg='red')
        sys.exit()

    mock_component = StackComponent(
        component_name,
        component_type='mock',
        project_path=os.getcwd(),
        resource_package=RESOURCE_PACKAGE,
    )

    status = mock_component.toggle_component()

    click.secho("Stack component `{}` has been {}.".format(component_name, status), fg='yellow')


@click.command()
@click.option("--component", help="Optionally limit test to single component.")
def stackTest():
    """Test inputs and outputs of stack or stack components.

    Stack test will mock inputs; queue, rest, or both depending on the nature
    of each stack component."""

     # click.echo("Mock testing the following stack components: {}".format())
     # click.secho("Mocked input for {}:{} ")
    pass


@click.command()
def build_tag_push():
    """Build, Tag, & Push all services to your docker registry."""
    click.echo(subprocess.getoutput('honcho run python bin/build-tag-push.py'))


main.add_command(readySystem, name='ready-system')
main.add_command(checkSystem, name='check-system')
main.add_command(updateDotenv, name='update-dotenv')
main.add_command(createProject, name='create-project')
main.add_command(generateStackComponent, name='generate-stack-component')
main.add_command(generateMock, name='generate-mock')
main.add_command(toggleMock, name='toggle-mock')
main.add_command(build_tag_push, name='build-tag-push')
