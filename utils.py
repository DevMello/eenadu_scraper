
import yaml
import logging

def load_config():
    """Loads the configuration from config.yaml."""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def load_proxies():
    """Loads a list of proxies from proxies.txt."""
    with open('proxies.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

def setup_logging():
    """Sets up logging to file."""
    logging.basicConfig(filename='errors.log', 
                        level=logging.ERROR,
                        format='%(asctime)s - %(levelname)s - %(message)s')

