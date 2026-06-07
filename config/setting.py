import os
import sys

from utils.data.yaml_reader import read_yaml

DIR_PATH = os.path.dirname(os.path.dirname(__file__))
sys.path.append(DIR_PATH)

FILE_PATH = {
    'project_config': os.path.join(DIR_PATH, 'config', 'project_config.yaml'),
    'app_config': os.path.join(DIR_PATH, 'config', 'app_config.yaml'),
    'log': os.path.join(DIR_PATH, 'logs'),

}

project_config = read_yaml(FILE_PATH['project_config'])
app_config = read_yaml(FILE_PATH['app_config'])
