import os
import shutil
import sys

import yaml


class YamlConfig:
    def __init__(self, filename: str):
        standard_config = None  # устанавливается если запускается exe и конфиг уже существует

        if hasattr(sys, "_MEIPASS"):
            from_filename = os.path.join(sys._MEIPASS, filename)
            if not os.path.exists(filename):
                to_filename = os.path.join(os.path.dirname(sys.executable), filename)
                shutil.copy(from_filename, to_filename)
            else:
                standard_config = from_filename
        else:
            filename = os.path.join(os.path.dirname(sys.argv[0]), "..", "..", "resources", filename)

        with open(filename, encoding="utf8") as file:
            self.data = yaml.safe_load(file)

        if standard_config is not None:
            with open(standard_config, encoding="utf8") as file:
                standard_data = yaml.safe_load(file)
            anything_wrote = False
            new_dict = {}
            for key, value in standard_data.items():
                if key in self.data:
                    new_dict[key] = self.data[key]  # для того чтобы вставлять поля по порядку
                else:
                    anything_wrote = True
                    new_dict[key] = value
            if anything_wrote:
                self.data = new_dict
                with open(filename, 'w', encoding="utf8") as file:
                    yaml.safe_dump(new_dict, file, sort_keys=False)

    def __getattr__(self, item):
        return self.data[item]
