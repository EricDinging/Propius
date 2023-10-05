import ruamel.yaml
import os

propius_config_file = './propius/global_config.yml'


def test_config(propius_data):
    pass


if __name__ == "__main__":
    client_manager_num = 1
    client_manager_ip_start = 50003
    client_db_port_start = 6380


    yaml = ruamel.yaml.YAML()
    with open(propius_config_file, 'r') as propius_config_yaml_file:
        propius_data = yaml.load(propius_config_yaml_file)


    with open(propius_config_file, 'w') as propius_config_yaml_file:
        yaml.dump(propius_data, propius_config_yaml_file) 