#!/usr/bin/env python

import os
import subprocess
import time
import yaml
import logging
import sys

log = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(name)s %(message)s'))
out_hdlr.setLevel(logging.INFO)
log.addHandler(out_hdlr)
log.setLevel(logging.INFO)

# Get docker login credentials.
docker = dict()
docker['DOCKER_USER'] = os.environ.get('DOCKER_USER')
docker['DOCKER_PASSWORD'] = os.environ.get('DOCKER_PASSWORD')
docker['DOCKER_EMAIL'] = os.environ.get('DOCKER_EMAIL')
docker['DOCKER_REGISTRY'] = os.environ.get('DOCKER_REGISTRY')

nones = set()
for env_var in [(k,v) for k,v in docker.items()]:
    if env_var[1] == None:
        log.error('Missing environment variable {}'.format(env_var[0]))
        nones.add(env_var[1])
if None in nones:
    log.error("""
              Please add missing environment variables to your environment.
              """)
    exit(1)

# Login to docker registry for this project and abort if it fails.
subprocess.check_call(["docker", "login", "-u", docker['DOCKER_USER'], "-p", docker["DOCKER_PASSWORD"], "-e",
                       docker["DOCKER_EMAIL"], "https://"+docker["DOCKER_REGISTRY"]])

# Generate Docker image tag using timestamp.
version = str(int(time.time()))

input_file = os.environ.get("DOCKER_COMPOSE_YML", "docker-compose.yml")
output_file = os.environ.get("DOCKER_COMPOSE_YML", "docker-compose-{}.yml".format(version))

if input_file == output_file == "docker-compose.yml":
    log.error("""
              I will not clobber docker-compose.yml file.
              Unset DOCKER_COMPOSE_YML or set it to something else.
              """)
    exit(1)

log.info("Input file: {}".format(input_file))
log.info("Output file: {}".format(output_file))

# Get the name of the current directory.
project_name = os.path.basename(os.path.realpath("."))

# Execute "docker-compose build" and abort if it fails.
subprocess.check_call(['docker-compose', '-f', input_file, 'build'])

# Load the services from the input docker-compose.yml file.
stack = yaml.load(open(input_file))

# Iterate over all services that have a "build" definition.
# Tag them and initiate a push in the background.
push_operations = dict()
for service_name, service in stack.items():
    if "build" in service:
        compose_image = "{}_{}:{}".format(project_name, service_name, "latest")
        log.info(compose_image)
        registry_image = "{}/{}:{}".format(docker['DOCKER_REGISTRY'], service_name, version)
        log.info(registry_image)
        # Re-tag the image so that it can be uploaded to the Registry.
        subprocess.check_call(["docker", "tag", compose_image, registry_image])
        # Spawn "docker push" to upload the image.
        push_operations[service_name] = subprocess.Popen(["docker", "push", registry_image])
        # Replace the "build" definition by and "image" definition,
        # using the name of the image on the Registry.
        del service["build"]
        service["image"] = registry_image

# Wait for push operations to complete.
for service_name, popen_object in push_operations.items():
    log.info("Waiting for {} push to complete...".format(service_name))
    popen_object.wait()
    log.info("Push to registry complete.")

# Write the new docker-compose.yml file.
with open(output_file, "w") as f:
    yaml.safe_dump(stack, f, default_flow_style=False)

log.info("New docker-compose file written to {}".format(output_file))
