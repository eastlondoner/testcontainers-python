#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import sqlalchemy
from selenium import webdriver

from testcontainers.core.config import ContainerConfig
from testcontainers.core.docker_client import DockerClient

from testcontainers.core.waiting_utils import wait_container_is_ready


class DockerContainer(object):
    def __init__(self, image_name, version):
        self._docker = DockerClient()
        self._config = ContainerConfig(image_name=image_name, version=version)

    def __enter__(self):
        return self.start()

    def __exit__(self, type, value, traceback):
        self.stop()

    def start(self):
        self._docker.run(image=self._config.image,
                         bind_ports=self._config.port_bindings,
                         env=self._config.environment,
                         links=self._config.container_links,
                         name=self._config.container_name)
        return self

    def stop(self):
        self._docker.remove_all_spawned()

    @property
    def host_ip(self):
        return self._config.host_ip

    @property
    def host_port(self):
        return self._config.host_port

    def get_env(self, key):
        return self._config.environment[key]

    def add_env(self, key, value):
        self._config.add_env(key, value)

    def bind_ports(self, host, container):
        self._config.bind_ports(host, container)


class GenericDbContainer(DockerContainer):
    def __init__(self, image_name,
                 version,
                 host_port,
                 user,
                 password,
                 database,
                 root_password):
        super(GenericDbContainer, self).__init__(image_name=image_name, version=version)
        self._config.set_host_port(host_port)
        self.user = user
        self.password = password
        self.database = database
        self.root_password = root_password
        self._configure()

    def start(self):
        """
        Start my sql container and wait to be ready
        :return:
        """
        super(GenericDbContainer, self).start()
        self._connect()
        return self

    @wait_container_is_ready()
    def _connect(self):
        """
        dialect+driver://username:password@host:port/database
        :return:
        """
        engine = sqlalchemy.create_engine(
            "{}://{}:{}@{}/{}".format(self._config.image_name,
                                      self.user,
                                      self.password,
                                      self.host_ip,
                                      self.database))
        engine.connect()

    def _configure(self):
        raise NotImplementedError()

    @property
    def host_ip(self):
        return "0.0.0.0"


class GenericSeleniumContainer(DockerContainer):
    def __init__(self, config):
        super(GenericSeleniumContainer, self).__init__(config)

    @wait_container_is_ready()
    def _connect(self):
        return webdriver.Remote(
            command_executor=('http://{}:{}/wd/hub'.format(
                self.host_ip,
                self.host_port)
            ),
            desired_capabilities=self._config.capabilities)

    def get_driver(self):
        return self._connect()

    def _is_chrome(self):
        return self._config.capabilities["browserName"] == "chrome"