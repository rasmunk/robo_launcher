from bin import RoboLauncher
from definitions import ROOT_DIR
import unittest


class TestRoboLauncher(unittest.TestCase):

    def test_start_stop(self):
        RoboLauncher.start()
        #active_containers = RoboLauncher.client.containers.list()
        #active_containers.__contains__(RoboLauncher.get_active_containers())

if __name__ == "__main__":
    RoboLauncher.start()

   # for i in range(0,9):
    #    RoboLauncher.start()

    #RoboLauncher.stop()


