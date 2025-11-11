# Лабораторная работа №2. Создание генератора с элементами ряда Фибоначчи

## Задание

Лабораторная работа состоит из двух подзаданий:

1. Создание сопрограммы на основе кода, позволяющей по данному n сгенерировать список элементов из ряда Фибоначчи.
2. Создание программы, возвращающей список чисел Фибоначчи с помощью итератора.

Рассмотрим особенности каждого из них.

## Задание 1

Стартовый борд:

На основе приложенного кода в файле gen_fib.py разработать сопрограмму (корутину), реализующую возвращение списка элементов ряда Фибоначчи.

```
>> gen = my_genn()

>> gen.send(3) 
[0, 1, 1] 

>> gen.send(5) 
[0, 1, 1, 2, 3] 

>> gen.send(8) 
[0, 1, 1, 2, 3, 5, 8, 13] 
```

Требуется написать необходимые тесты в файле test_fib.py.

## Задание 2

Дополните код классом FibonacchiLst (пример такого класса представлен в even_numbers_iterator.py), который бы позволял перебирать элементы из ряда Фибоначчи по данному ей списку. Итератор должен вернуть очередное значение, которое принадлежит ряду Фибоначчи, из данного ей списка. Например: для lst = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1], FibonacchiLst должен вернуть [0, 1, 2, 3, 5, 8, 1]

Решение может быть выполнено с помощью реализации содержимого методов __init__,__iter__, __next__ или с помощью реализации метода __getitem__.

```
class FibonacchiLst:
    def __init__(self):
        pass
    
    def __iter__(self):
        pass 

    def __next__(self):
        pass
```

Пример реализации итератора, возвращающего четные элементы, из iterable-объекта представлен в файле even_numbers_iterator.py.

## Решение

## Задание 1

Решение:
```
import functools
import itertools

def fib_elem_gen():
    """Генератор, возвращающий элементы ряда Фибоначчи"""
    a = 0
    b = 1

    while True:
        yield a
        res = a + b
        a = b
        b = res

def fib_coroutine(g):
    @functools.wraps(g)
    def inner(*args, **kwargs):
        gen = g(*args, **kwargs)
        gen.send(None)
        return gen
    return inner

@fib_coroutine        
def my_genn():
    """Сопрограмма"""
    
    fib_gen = fib_elem_gen()
    
    while True:
        number_of_fib_elem = yield
        l = list(itertools.islice(fib_gen, number_of_fib_elem))
        yield l  
```
[Ссылка на код](https://github.com/ZabivakaXD/Herzen_curse_3/blob/main/prog/lab-2/gen-fib.py)

Тесты:
![1.png](https://github.com/ZabivakaXD/Herzen_curse_3/blob/main/prog/lab-2/img/1.png)

[Ссылка на код](https://github.com/ZabivakaXD/Herzen_curse_3/blob/main/prog/lab-2/test-fib.py)

## Задание 2

Решение:
```
class FibonacchiLst:
    
    def __init__(self, instance):
        self.instance = instance   
        self.idx = 0  # инициализируем индекс для перебора элементов
        
        
    def __iter__(self):
        return self  # возвращает экземпляр класса, реализующего протокол итераторов
    
    
    def __next__(self):  # возвращает следующий по порядку элемент итератора
        while True:
            try:
                res = self.instance[self.idx]  # получаем очередной элемент из iterable
                
            except IndexError:
                raise StopIteration

            if self._is_fibonacci(res):  # проверяем, является ли число числом Фибоначчи
                self.idx += 1  # если да, возвращаем значение и увеличиваем индекс
                return res

            self.idx += 1  # если нет, то просто увеличиваем индекс
    
    
    def _is_fibonacci(self, n):
        """Проверяет, является ли число числом Фибоначчи"""
        if n < 0:
            return False
            
        # Проверяем, является ли число полным квадратом для формулы:
        # n является числом Фибоначчи тогда и только тогда, когда
        # 5*n*n + 4 или 5*n*n - 4 является полным квадратом
        
        def is_perfect_square(x):
            root = int(x ** 0.5)
            return root * root == x
        
        return is_perfect_square(5 * n * n + 4) or is_perfect_square(5 * n * n - 4)
    
lst = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1]
print(list(FibonacchiLst(lst))) # [0, 1, 2, 3, 5, 8, 1]
```

[Ссылка на код](https://github.com/ZabivakaXD/Herzen_curse_3/blob/main/prog/lab-2/even_numbers_iterator.py)


