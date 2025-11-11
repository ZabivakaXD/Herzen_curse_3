import unittest

from gen_fib import my_genn

class TestFibonacciCoroutine(unittest.TestCase):
    
    def setUp(self):
        """Создаем новый генератор перед каждым тестом"""
        self.gen = my_genn()
    
    def test_three_elements(self):
        """Тест для 3 элементов"""
        result = self.gen.send(3)
        self.assertEqual(result, [0, 1, 1])
    
    def test_five_elements(self):
        """Тест для 5 элементов"""
        result = self.gen.send(5)
        self.assertEqual(result, [0, 1, 1, 2, 3])
    
    def test_eight_elements(self):
        """Тест для 8 элементов"""
        result = self.gen.send(8)
        self.assertEqual(result, [0, 1, 1, 2, 3, 5, 8, 13])
    
    def test_one_element(self):
        """Тест для 1 элемента"""
        result = self.gen.send(1)
        self.assertEqual(result, [0])
    
    def test_zero_elements(self):
        """Тест для 0 элементов"""
        result = self.gen.send(0)
        self.assertEqual(result, [])
    
    def test_large_number(self):
        """Тест для большего количества элементов"""
        result = self.gen.send(10)
        expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()