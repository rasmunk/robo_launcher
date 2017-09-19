import docker.errors, docker.types, requests.exceptions, time, os
from configparser import ConfigParser
from util import RoboContainerInterface
from util import ContainerConfig

config = ConfigParser()
config.read('../res/config.ini')
config.sections()
exp_prop = 'ExperimentProperties'
ea_prop = 'EAProperties'
nn_prop = 'NNProperties'
docker_prop = 'DockerProperties'
client = docker.from_env()


class RoboLauncher:
    @staticmethod
    def error_message(args):
        print("Invalid parameter: " + args[0] + " allowed values: " + args[1])
        exit(1)

    @staticmethod
    def stringify_list(list):
        return str(list).strip('[').strip(']')

    @staticmethod
    def stringify_range_list(list):
        return str(list).strip('[').strip(']').strip(' ').replace(', ', '-')

    @staticmethod
    def valid_parameters():
        list_valid_num_robots = [1, 6]
        # TODO -> query infrastructure for supported robot types
        list_valid_robot_types = ['Thymio']
        # TODO -> query infrastructure for supported experiments
        list_valid_experiments = ['hunter-prey-selfish', 'hunter-prey-reciprocator']
        list_valid_num_generations_range = [1, 50000]
        list_valid_num_population_range = [1, 100]
        list_valid_mutation_rate_range = [0.1, 1.0]
        list_valid_mutation_types = ['each_gene', 'entire_chromosome']
        list_valid_chromo_representation = ['binary', 'float']
        list_valid_num_hidden_layers = [0, 5]
        list_valid_num_hidden_nodes = [0, 10]
        list_valid_active_bias = [True, False]

        if config.getint(exp_prop, 'num_robots') < list_valid_num_robots[0] or config.getint(exp_prop, 'num_robots') > \
                list_valid_num_robots[1]:
            RoboLauncher.error_message(['num_robots', RoboLauncher.stringify_range_list(list_valid_num_robots)])

        if config.get(exp_prop, 'robot_type') not in list_valid_robot_types:
            RoboLauncher.error_message(['robot_type', RoboLauncher.stringify_list(list_valid_robot_types)])

        if config.get(exp_prop, 'experiment_type') not in list_valid_experiments:
            RoboLauncher.error_message(['experiment_type', RoboLauncher.stringify_list(list_valid_experiments)])

        if config.getint(ea_prop, 'num_generations') < list_valid_num_generations_range[0] or config.getint(ea_prop, 'num_generations') > \
                list_valid_num_generations_range[1]:
            RoboLauncher.error_message(['num_generations', RoboLauncher.stringify_range_list(list_valid_num_generations_range)])

        if config.getint(ea_prop, 'population_size') < list_valid_num_population_range[0] or config.getint(ea_prop, 'population_size') > \
                list_valid_num_population_range[1]:
            RoboLauncher.error_message(['population_size', RoboLauncher.stringify_range_list(list_valid_num_population_range)])

        if config.getfloat(ea_prop, 'mutation_rate') < list_valid_mutation_rate_range[0] or config.getfloat(ea_prop, 'mutation_rate') > \
                list_valid_mutation_rate_range[1]:
            RoboLauncher.error_message(['mutation_rate', RoboLauncher.stringify_range_list(list_valid_mutation_rate_range)])

        if config.get(ea_prop, 'mutation_type') not in list_valid_mutation_types:
            RoboLauncher.error_message(['mutation_type', RoboLauncher.stringify_list(list_valid_mutation_types)])

        if config.get(ea_prop, 'chromosome_representation') not in list_valid_chromo_representation:
            RoboLauncher.error_message(['chromosome_representation', RoboLauncher.stringify_list(list_valid_chromo_representation)])

        if config.getint(nn_prop, 'num_hidden_layers') < list_valid_num_hidden_layers[0] or config.getint(nn_prop, 'num_hidden_layers') > \
                list_valid_num_hidden_layers[1]:
            RoboLauncher.error_message(['num_hidden_layers', RoboLauncher.stringify_range_list(list_valid_num_hidden_layers)])

        if config.getint(nn_prop, 'num_hidden_nodes') < list_valid_num_hidden_nodes[0] or config.getint(nn_prop, 'num_hidden_nodes') > \
                list_valid_num_hidden_nodes[1]:
            RoboLauncher.error_message(['num_hidden_nodes', RoboLauncher.stringify_range_list(list_valid_num_hidden_nodes)])

        if config.getboolean(nn_prop, 'active_bias') not in list_valid_active_bias:
            RoboLauncher.error_message(['active_bias', RoboLauncher.stringify_list(list_valid_active_bias)])

    @staticmethod
    def start():
        RoboLauncher.valid_parameters()
        list_active_containers = []
        # Setup Docker network
        print("Setting up docker network")
        ipam_poll = docker.types.IPAMPool(subnet=config.get(docker_prop, 'network_subnet'))
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_poll])
        try:
            # if already exists, disconnect and recreate the network from fresh
            sim_network = client.networks.get(config.get(docker_prop, 'network_name'))
            for container in sim_network.containers:
                sim_network.disconnect(container)
            sim_network.remove()
        except Exception as e:
            pass
        client.networks.create(config.get(docker_prop, 'network_name'), driver="bridge", ipam=ipam_config)
        # Jump out of src directory
        os.chdir("..")
        print("Launching Engine")
        # # Launch engine
        engine = RoboContainerInterface(repo=config.get(docker_prop, 'engine_repo'), branch=config.get(docker_prop, 'engine_branch'),
                                        name=config.get(docker_prop, 'engine_name'),
                                        network=config.get(docker_prop, 'network_name'))
        # engine.set_container_config(container_config=ContainerConfig())
        list_active_containers.append(engine.start())

        print("Launching Robots")
        list_robots = []
        # # Launch robots
        for idx in range(config.getint(exp_prop, 'num_robots')):
            list_robots.append(
                RoboContainerInterface(repo=config.get(docker_prop, 'robot_repo'), branch=config.get(docker_prop, 'robot_branch'),
                                       name=config.get(docker_prop, 'robot_name'), network=config.get(docker_prop, 'network_name')))
            list_active_containers.append(list_robots[idx].start())

        print("Launching Simulator")
        # # Launch simulator
        sim = RoboContainerInterface(repo=config.get(docker_prop, 'simulator_repo'), branch=config.get(docker_prop, 'robot_branch'),
                                     name=config.get(docker_prop, 'simulator_name'),
                                     network=config.get(docker_prop, 'network_name'))
        list_active_containers.append(sim.start())
        # Save launched container id's
        try:
            f = open("experiment_" + str(int(time.time())) + ".txt", "w")
            for container in list_active_containers:
                f.write(container.id + "\n")
            f.close()
        except IOError as e:
            print(e)
            print("Failed to save experiment file container the container id's")
        print("Finished")

    @staticmethod
    def stop():
        print("Stopping infrastructure")
        my_containers = {}
        os.chdir("..")
        for file in os.listdir("."):
            if file.startswith("experiment_"):
                my_containers[file] = []
                try:
                    f = open(file)
                    for line in f:
                        my_containers[file].append(line.strip('\n'))
                except IOError as e:
                    print("Failed to load experiment file, " + file)

        # Stop my experiment containers
        for file, containers in my_containers.items():
            for container_id in containers:
                try:
                    client.containers.get(container_id).remove(v=True, link=False, force=True)
                except docker.errors.NotFound:
                    print("Container id: " + container_id + " doesn't appear to be running")

        # Remove experiment files
        for key, value in my_containers.items():
            try:
                print("Removing: " + key)
                os.remove(key)
            except NotImplementedError as e:
                print("Failed to remove file: " + key)

    @staticmethod
    def clean():
        print("Cleaning infrastructure")
        list_images = client.images.list()
        for image in list_images:
            for tag in image.tags:
                if config.get(docker_prop, 'engine_name') in tag or config.get(docker_prop, 'robot_name') in tag or \
                                config.get(docker_prop, 'simulator_name') in tag:
                    client.images.remove(image)


# if __name__ == "__main__":
#     commands = {
#         'start': RoboLauncher.start,
#         'stop': RoboLauncher.stop,
#         'clean': RoboLauncher.clean
#     }
#     # Initialize Docker
#     try:
#         client.ping()
#     except requests.exceptions.ConnectionError as e:
#         print("Failed to connect to Docker, are you sure docker is running")
#         exit(-1)
#
#     commands.get(config['Infrastructure']['command'])()
