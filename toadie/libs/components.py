__version__="0.1.0"
__copyright__="Copyright (C) 2016 David Gonzalez"
__author__="David 'Gonzo' Gonzalez"
__license__="Apache License 2.0"

import os
import sys
import logging
import yaml
from collections import defaultdict
from yaml.representer import Representer
import re
import pkg_resources
import click


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger(__name__)

yaml.add_representer(defaultdict, Representer.represent_dict)


class StackComponent(object):
    """This class generates stack components of type:
        - `service`,
        - `test`, or
        - `mock`

    with interfaces of type
        - `queue`,
        - `rest`, and
        - `hybrid`."""
    def __init__(self,
                 component_name,
                 component_type,
                 project_path,
                 resource_package,
                 verbose=False):
        self.component_name = component_name
        self.component_type = component_type
        self.project_dir = project_path
        self.resource_package = resource_package
        self.verbose = verbose
        self.parent_dir = os.path.join(project_path, component_type+"s")
        self.dotenv = os.path.join(self.project_dir, '.env')
        if not os.path.exists(self.parent_dir):
            os.mkdir(self.parent_dir)

        self.component_dir = os.path.join(self.parent_dir, component_name)
        if not os.path.exists(self.component_dir):
            os.mkdir(self.component_dir)

    def define_run(self):
        """Generate run script to be sourced in Dockerfile."""
        contents = "#!/bin/sh\n"
        with open(os.path.join(self.component_dir, 'run.sh'), 'w') as _:
            _.write(contents)


    def define_dockerfile(self,
                          default_baseimage="python:alpine",):
        """Generate Dockerfile that will be used by docker-compose."""
        resource_path = os.path.join('templates', 'app.py')
        template = pkg_resources.resource_string(
            self.resource_package, resource_path)
        dockerfile = template.decode('utf-8').replace(r'{{python:alpine}}', 'python:alpine')
        with open(os.path.join(self.component_dir, 'Dockerfile'), 'w') as _:
            _.write(dockerfile)


    def add_lines_to_env(self, env_vars):
        # Check contents of dotenv.example.
        env_var_names = set()
        with open(self.dotenv, 'r') as _:
            lines = _.read().splitlines()
            for line in lines:
                k, v = line.split("=")
                env_var_names.add(k)

        if set(env_vars) not in env_var_names:
            for var in env_vars:
                env_var = "{}=__blank__".format(var)
                with open(self.dotenv, 'a') as _:
                    _.write(env_var+"\n")
                    click.secho("""
                                Added to .env:
                                {}
                                Please update.""".format(env_var),
                                fg='yellow')


    def update_docker_compose(self,
                              default_rabbit_link="rabbitmq",
                              toggle=False):
        """Generate docker-compose.yml"""
        dc_filepath = os.path.join(self.project_dir, 'docker-compose.yml')
        with open(dc_filepath, 'r') as _:
            docker_compose = yaml.load(_)
            # Ready docker-compose for munging.
            docker_compose.pop('version')

        # this refers to docker-compose.yml version 2 services entry
        if 'services' not in docker_compose:
            docker_compose['services'] = dict()

        # Check if queue dependencies are already declared. Add if missing.
        if 'rabbitmq' not in docker_compose['services']:
            queue_stack = defaultdict(dict)
            queue_stack['rabbitmq']['image'] = 'rabbitmq:management'
            queue_stack['rabbitmq']['ports'] = ["5672:5672", "15672:15672"]
            queue_stack['rabbitmq']['env_file'] = [".env"]
            docker_compose['services'].update(queue_stack)
            env_vars = [
                "RABBITMQ_DEFAULT_USER",
                "RABBITMQ_DEFAULT_PASS"
            ]

            self.add_lines_to_env(env_vars)

        if toggle and self.component_name in docker_compose['services']:
            # Remove entry
            docker_compose['services'].pop(self.component_name)
            status = 'disabled'
        else:
            # Add new service components to stack.
            new_service = defaultdict(dict)
            _, parent_rel_dir = os.path.split(self.parent_dir)
            new_service[self.component_name]['build'] = './{}/{}'.format(
                parent_rel_dir, self.component_name)

            if re.match(r"^mock_for.*", self.component_name):
                real_component_name = re.sub(r'^mock_for_(.*)', r'\g<1>', self.component_name)
                links = [default_rabbit_link, real_component_name]
            else:
                links = [default_rabbit_link,]

            new_service[self.component_name]['links'] = links
            docker_compose['services'].update(new_service)
            status = 'enabled'

        with open(os.path.join(self.project_dir, 'docker-compose.yml'), 'w') as _:
            _.write("version: '2.0'\n")
            _.write(yaml.dump(docker_compose, default_flow_style=False))

        return status

    def add_logqueue(self, promise, log_exchange):
        promise['logqueue']['bindings'] = dict(topic=[
            "{}.log.INFO".format(self.component_name),
            "{}.log.DEBUG".format(self.component_name),
            "{}.log.ERROR".format(self.component_name),
        ])
        promise['logqueue']['exchange'] = log_exchange
        return promise


    def add_errqueue(self, promise, log_exchange):
        promise['errqueue']['bindings'] = {'topics': ['{}.ERROR'.format(self.component_name)]}
        promise['errqueue']['exchange'] = log_exchange
        return promise


    def define_promise_yml(self, mock=False):
        '''Create promise.yml file.'''
        # Create boilerplate services.
        component_promise = dict()
        component_promise['{}'.format(self.component_name)] = defaultdict(dict)
        promise = component_promise['{}'.format(self.component_name)]

        if self.component_name not in ['logger', 'errlogger']:
            log_exchange = {'name':'logExchange', 'type':'direct'}
            promise.update(self.add_logqueue(promise, log_exchange))
            promise.update(self.add_errqueue(promise, log_exchange))

        # Boilerplate component topic exchange.
        component_exchange = {
            'name':'{}Exchange'.format(self.component_name),
            'type':'topic'}
        # Create boilerplate inqueue and add to promise.
        if not mock:
            inqueue = defaultdict(dict)
            inqueue['bindings'] = {'topics': ['{}.IN.#'.format(self.component_name)]}
            inqueue['exchange'] = component_exchange
            inqueue['name'] = '{}InQueue0'.format(self.component_name)
            inqueue['body']['message'] = 'Hello, from {}'.format(inqueue['name'])
            inqueue['body']['format'] = 'text'
            promise['inqueues'] = list()
            promise['inqueues'].append(inqueue)
        # Create boilerplate outqueue and add to promise.
        outqueue = defaultdict(dict)
        outqueue['bindings'] = {'topics': ['{}.OUT'.format(self.component_name)]}
        outqueue['exchange'] = component_exchange
        outqueue['name'] = '{}OutQueue0'.format(self.component_name)
        outqueue['body']['message'] = 'Hello, from {}'.format(outqueue['name'])
        outqueue['body']['format'] = 'text'
        promise['outqueues'] = list()
        promise['outqueues'].append(outqueue)
        target_path = os.path.join(self.component_dir, 'promise.yml')
        with open(target_path, 'w') as _:
            _.write(yaml.dump(component_promise, default_flow_style=False))


    def define_requirments(self):
        """Generate requirements.txt file."""
        target_path = os.path.join(self.component_dir, 'requirements.txt')
        requirements = ['pika',]
        with open(target_path, 'a') as _:
            for req in requirements:
                _.write(req+"\n")


    def create_queue_component(self):
        """Queue based services have:

            \b
            Templates:
                - promise.yml
                - run.sh
                - Dockerfile
                - comsume.py
                - produce.py
        """

        self.define_run()
        self.define_dockerfile()
        self.update_docker_compose()
        self.define_promise_yml()
        self.define_requirments()


    def create_mock_component(self):
        """Create mock component files."""
        self.define_run()
        self.define_dockerfile()
        self.define_promise_yml(mock=True)
        self.define_requirments()


    def toggle_component(self):
        """Enable/disable mock component."""
        status = self.update_docker_compose(toggle=True)
        return status


    def create_rest_service(self, name, inqueue, outqueue):
        pass


    def create_hybrid_service(self, name, inqueue, outqueue):
        pass
