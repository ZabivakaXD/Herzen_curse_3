# Лабораторная работа №1. Реализация удаленного импорта

## Задание

Разместите представленный ниже код локально на компьютере и реализуйте механизм удаленного импорта. Продемонстрируйте в виде скринкаста или в текстовом отчете с несколькими скриншотами работу удаленного импорта.

## По шагам:

1. Создайте файл myremotemodule.py, который будет импортироваться, разместите его в каталоге, который далее будет "корнем сервера" (допустим, создайте его в папке rootserver).
2. Разместите в нём следующий код:
```
def myfoo():
    author = "" # Здесь обознаться своё имя (авторство модуля)
    print(f"{author}'s module is imported")
```
3. Создайте файл Python с содержимым функций url_hook и классов URLLoader, URLFinder из текста конспекта лекции со всеми необходимыми библиотеками (допустим, activation_script.py).
4. Далее, чтобы продемонстрировать работу импорта из удаленного каталога, мы должны запустить сервер http так, чтобы наш желаемый для импорта модуль "лежал" на сервере (например, в корневой директории сервера). Откроем каталог rootserver с файлом myremotemodule.py и запустим там сервер:
```
python3 -m http.server
```
5. После этого мы запускаем файл, в котором содержится код, размещенный выше (обязательно добавление в sys.path_hooks).
```
python3 -i activation_script.py
```
6. Теперь, если мы попытаемся импортировать файл myremotemodule.py, в котором размещена наша функция myfoo будет выведен ModuleNotFoundError: No module named 'myremotemodule', потому что такого модуля пока у нас нет (транслятор про него ничего не знает).
7. Однако, как только мы выполним код:
```
sys.path.append("http://localhost:8000")
```
добавив путь, где располагается модуль, в sys.path, будет срабатывать наш "кастомный" URLLoader. В path_hooks будет содержатся наша функция url_hook.
8. Протестируйте работу удаленного импорта, используя в качестве источника модуля другие "хостинги" (например, repl.it, github pages, beget, sprinthost).
9. Переписать содержимое функции url_hook, класса URLLoader с помощью модуля requests (см. комменты).
10. Задание со звездочкой (*): реализовать обработку исключения в ситуации, когда хост (где лежит модуль) недоступен.
11. Задание про-уровня (***): реализовать загрузку пакета, разобравшись с аргументами функции spec_from_loader и внутренним устройством импорта пакетов.

## Решение:

Делал все по шагам как и было описанно зарание.

Подтверждение шагов:

Запуск сервера.

![1.png](https://github.com/ZabivakaXD/Herzen_curse_3/blob/main/prog/lab-1/img/1.png)

Подключение нашего модуля без указания пути.

![2.png](https://github.com/ZabivakaXD/Herzen_curse_3/blob/main/prog/lab-1/img/2.png)

Подключение нашего модуля через Github.

![3.png](https://github.com/ZabivakaXD/Herzen_curse_3/blob/main/prog/lab-1/img/3.png)

Обработка ошибки подключения к хосту.

![4.png](https://github.com/ZabivakaXD/Herzen_curse_3/blob/main/prog/lab-1/img/4.png)

[Ссылка на код](https://github.com/ZabivakaXD/Herzen_curse_3/blob/main/prog/lab-1/activation_script.py)

```
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
```