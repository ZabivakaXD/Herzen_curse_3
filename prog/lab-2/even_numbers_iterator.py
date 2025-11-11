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
