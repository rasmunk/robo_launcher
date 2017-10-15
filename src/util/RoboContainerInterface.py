import os, docker.client, docker.errors
from git import Repo


# Class wrapper for retrieving a docker file and building the image and launching the container
class RoboContainerInterface:
    client = docker.from_env()
    id = None
    name = None
    network = None
    container_config = None

    def __init__(self, repo, branch, name, network):
        self.name = name
        self.network = network
        # Retrieve source code and build the docker image
        target_dir = self.name + '.git'
        full_dir = os.getcwd() + "/" + target_dir
        list_files = os.listdir(".")
        if target_dir not in list_files:
            repo = Repo.clone_from(repo,
                                   to_path=full_dir, branch=branch)
        else:
            repo = Repo(target_dir)
            origin = repo.remotes.origin
            origin.pull()

        self.client.images.build(path=full_dir, tag=self.name)

    # Launch the built docker container
    # Returns a container object
    # Returns when the container is running
    def start(self):
        container = self.client.containers.run(image=self.name, network=self.network, stdin_open=True, detach=True, tty=True,
                                          environment=dict(self.container_config.config))
        running = False
        while running is False:
            try:
                self.client.containers.get(container.attrs['Id'])
                self.id = container.attrs['Id']
                running = True
            except docker.errors.NotFound:
                pass
        return container

    # Stop the docker container
    def stop(self):
        container = self.client.containers.get(self.id)
        container.stop()

    def inspect(self):
        inspection = self.client.inspect_container()
        return inspection

    def network_containers(self):
        networks = self.client.containers.get(self.id).attrs['NetworkSettings']['Networks']
        return networks

    def remove(self):
        container = self.client.containers.get(self.id)
        container.remove()

    def set_container_config(self, container_config):
        self.container_config = container_config
