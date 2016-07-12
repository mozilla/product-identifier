import importlib


def load_config_obj(obj_name):
    tokens = obj_name.split(".")
    module_name = ".".join(tokens[:-1])
    class_name = tokens[-1]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)
