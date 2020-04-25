import os
import re
from pathlib import Path

from testcontainers import mysql

from testcontainers.core.generic import GenericContainer
from testcontainers.core.utils import inside_container
from importlib import reload


def setup_module(m):
    os.environ["MYSQL_USER"] = "demo"
    os.environ["MYSQL_DATABASE"] = "custom_db"


def test_docker_custom_image():
    container = GenericContainer("mysql:5.7.17")
    container.with_exposed_ports(3306)
    container.with_env("MYSQL_ROOT_PASSWORD", "root")

    with container:
        port = container.get_exposed_port(3306)
        assert int(port) > 0


def test_docker_env_variables():
    reload(mysql)

    db = mysql.MySqlContainer()
    db.with_bind_ports(3306, 32785)
    with db:
        url = db.get_connection_url()
        if inside_container():
            assert re.match(r'mysql\+pymysql://demo:test@(\d+\.){3}\d+:3306/custom_db', url)
        else:
            assert url == 'mysql+pymysql://demo:test@localhost:32785/custom_db'


def test_docker_kargs():
    code_dir = Path(__file__).parent
    container_first = GenericContainer("nginx:latest")
    container_first.with_volume_mapping(code_dir, '/code')

    container_second = GenericContainer("nginx:latest")

    with container_first:
        container_second.with_kargs(volumes_from=[container_first._container.short_id])
        with container_second:
            files_first = container_first.exec('ls /code').output.decode('utf-8').strip()
            files_second = container_second.exec('ls /code').output.decode('utf-8').strip()
            assert files_first == files_second
