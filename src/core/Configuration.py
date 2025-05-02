import os
import shutil
import sys

import yaml


class YamlConfig:
    def __init__(self, filename: str):
        if hasattr(sys, "_MEIPASS"):
            if not os.path.exists(filename):
                from_filename = os.path.join(sys._MEIPASS, filename)
                to_filename = os.path.join(os.path.dirname(sys.executable), filename)
                shutil.copy(from_filename, to_filename)
        else:
            filename = os.path.join(os.path.dirname(sys.argv[0]), "..", "..", "resources", filename)
        with open(filename, encoding="utf8") as file:
            self.data = yaml.safe_load(file)

    def __getattr__(self, item):
        return self.data[item]
