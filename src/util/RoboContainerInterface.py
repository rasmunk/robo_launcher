import os, docker.client
from git import Repo


# Class wrapper for retrieving a docker file and building the image and launching the container
class RoboContainerInterface:
    client = docker.from_env()
    name = None
    network = None

    def __init__(self, repo, branch, name, network):
        self.name = name
        self.network = network
        # Retrieve source code and build the docker image
        os.chdir("..")
        target_dir = self.name + '.git'
        full_dir = os.getcwd() + "/" + target_dir
        list_files = os.listdir(os.getcwd())
        if target_dir not in list_files:
            repo = Repo.clone_from(repo,
                                   to_path=full_dir, branch=branch)
        os.chdir(full_dir)
        self.client.images.build(path=full_dir, tag=self.name)

    # Launch the built docker container
    def start(self):
        self.client.containers.run(image=self.name, network=self.network, stdin_open=True, detach=True, tty=True)

    # Stop the docker container
    def stop(self):
        container = self.client.containers.get(self.name)
        container.stop()

    def remove(self):
        container = self.client.containers.get(self.name)
        container.remove()
