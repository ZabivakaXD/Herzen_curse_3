import re
import sys
import requests
from importlib.abc import PathEntryFinder, Loader
from importlib.util import spec_from_loader
from requests.exceptions import RequestException

class URLLoader(Loader):
    def create_module(self, target):
        return None
    def exec_module(self, module):
        try:
            response = requests.get(module.__spec__.origin)
            response.raise_for_status() 
            source = response.text
            code = compile(source, module.__spec__.origin, mode="exec")
            exec(code, module.__dict__)
        except RequestException as e:
            raise ImportError(f"Не удалось загрузить модуль с {module.__spec__.origin}: {e}")        
        
        
class URLFinder(PathEntryFinder):
    def __init__(self, url, available):
        self.url = url
        self.available = available
    def find_spec(self, name, target=None):
        if name in self.available:
            origin = "{}/{}.py".format(self.url, name)
            loader = URLLoader()
            return spec_from_loader(name, loader, origin=origin)
        else:
            return None
        

def url_hook(some_str):
    if not some_str.startswith(("http", "https")):
        raise ImportError
    try:
        response = requests.get(some_str)
        response.raise_for_status()
        data = response.text
        filenames = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*\.py", data)
        modnames = {name[:-3] for name in filenames}
        return URLFinder(some_str, modnames)
    except RequestException as e:
        print(f"Ошибка доступа к {some_str}: {e}")
        raise ImportError(f"Не удалось получить список модулей с {some_str}")
    
sys.path_hooks.append(url_hook)
print(sys.path_hooks)