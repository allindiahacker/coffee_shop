import copy
import unittest

from coffee_shop import take_order
from order_data import ORDER_DATA


class SimpleTest(unittest.TestCase):

    @staticmethod
    def test_for_given_input_data():
        data = copy.deepcopy(ORDER_DATA)
        take_order(data)

    def test_for_invalid_input_data(self):
        with self.assertRaises(Exception) as error:
            take_order({})
        self.assertEqual(str(error.exception), 'Input data is blank')

        with self.assertRaises(TypeError):
            take_order('abc')

    def test_for_all_quantities_exhausted(self):
        data = copy.deepcopy(ORDER_DATA)
        data['machine']['total_items_quantity'] = {
            "hot_water": 0,
            "hot_milk": 0,
            "ginger_syrup": 0,
            "sugar_syrup": 0,
            "tea_leaves_syrup": 0
        }
        take_order(data)


if __name__ == '__main__':
    unittest.main()
