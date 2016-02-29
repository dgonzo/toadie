import subprocess
from distutils.version import LooseVersion
import re
from collections import defaultdict
from sys import platform


DOCKER_ENGINE_URL = "https://docs.docker.com/engine/installation/linux/"
DOCKER_ENGINE_V = "1.10.1"
DOCKER_COMPOSE_URL = "https://docs.docker.com/compose/install/"
DOCKER_COMPOSE_V = "1.6.0"
DOCKER_MACHINE_URL = "https://docs.docker.com/machine/install-machine/"
DOCKER_MACHINE_V = "0.6.0"
DOCKER_TOOLBOX_URL = "https://www.docker.com/products/docker-toolbox"
CONDA_URL = "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh"
CONDA_V = "3.18.6"
VBOX_V = "5.0.14r105127"
VBOX_URL = "https://www.virtualbox.org/wiki/Downloads"


class Tools:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def get_platform_tools(self,tool):
        if platform == "linux" or "linux2":
            tools = {'docker':DOCKER_ENGINE_URL,
                     'docker-compose':DOCKER_COMPOSE_URL,
                     'docker-machine':DOCKER_MACHINE_URL,
                     'conda':CONDA_URL,
                     'vboxmanage':VBOX_URL}
        elif platform == "darwin":
            tools = {'docker':DOCKER_TOOLBOX_URL,
                     'conda':CONDA_URL,
                     'vboxmanage':DOCKER_TOOLBOX_URL}
        elif platform == "windows":
            tools = {'docker':DOCKER_TOOLBOX_URL,
                     'conda':CONDA_URL,
                     'vboxmanage':DOCKER_TOOLBOX_URL}
        return tools[tool]

    def check_tools(self):
        tool_statuses = defaultdict(dict)
        parse_tools = [
            ('docker','-v', DOCKER_ENGINE_V,
             re.compile(r'^Docker version (.*), .*'),
             DOCKER_ENGINE_URL),
            ('docker-compose','-v', DOCKER_COMPOSE_V,
             re.compile(r'^docker-compose version (.*), .*'),
             DOCKER_COMPOSE_URL),
            ('docker-machine','-v', DOCKER_MACHINE_V,
             re.compile(r'^docker-machine version (.*), .*'),
             DOCKER_ENGINE_URL),
            ('conda','-V', CONDA_V,
             re.compile(r'^conda (.*)'),
             CONDA_URL),
            ('vboxmanage','-v', VBOX_V,
             re.compile(r'(.*)$'),
             VBOX_URL)]
        for tool in parse_tools:
            install_url = self.get_platform_tools(tool[0])
            tool_statuses[tool[0]]['install_url'] = install_url
            try:
                parse_version = tool[3]
                version = parse_version.match(
                    subprocess.getoutput(tool[0]+" "+tool[1])).group(1)
            except:
                tool_statuses[tool[0]]['version'] = None
                tool_statuses[tool[0]]['version_passes'] = False
            else:
                version_passes = LooseVersion(version) >= LooseVersion(tool[2])
                tool_statuses[tool[0]]['version'] = version
                tool_statuses[tool[0]]['version_passes'] = version_passes
        return tool_statuses
