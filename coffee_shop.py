from multiprocessing import Lock, Process, Value

from order_data import ORDER_DATA


class CoffeeShop:

    def __init__(self, total_ingredients_quantity, beverages):
        """
        Initialising a CoffeeShop Instance to handle orders, here we take in the recipe(`beverages`) and
        ingredients(`total_ingredients_quantity`)
        :param total_ingredients_quantity: Dict containing quantity of each ingredient
        :param beverages: Dict containing recipe of list of ingredients and quantities needed for each beverage
        """
        self.total_ingredients_quantity = total_ingredients_quantity
        self.beverages = beverages
        self.low_ingredients = {}  # This dict can be used to check at any time which ingredients are low

        self.ingredients_lock = {}
        for ingredient in self.total_ingredients_quantity:
            # Creating individual lock objects per ingredient
            self.ingredients_lock[f'{ingredient}_lock'] = Lock()
            # Making each ingredient a Value object to secure the quantity updation happens according to lock
            self.total_ingredients_quantity[ingredient] = Value('i', self.total_ingredients_quantity[ingredient])

    def _release_locks(self):
        """
        Internal method to handle release of lock on respective ingredients
        :return: None
        """
        for lock in self.ingredients_lock:
            try:
                self.ingredients_lock[lock].release()
            except ValueError:
                continue

    def update_ingredient_low_indicator(self, ingredient, quantity):
        self.low_ingredients.update({ingredient: quantity})

    def process_order(self, beverage):
        """
        This method will run in an independent thread(asynchronously), we will try to process the order
        here whilst updating ingredients.

        This method will run in 3 steps
        Step 1: Check if all ingredients exist
        Step 2: Check if each needed ingredient has sufficient quantity
               (^Whilst taking locks on those ingredients sequentially)
        Step 3: Updating of respective ingredients, this step only occurs if we have all the ingredients present in
                sufficient quantity.

        Note: At any given point during Step 2 if any ingredient is not present, we release the lock on each ingredient
        to allow other processes to use those ingredients.

        At the end, post the beverage is made, we release the relevant locks on ingredient.

        We are acquiring a lock on relevant ingredients since ingredients are a shared resource amongst
        the concurrent processes. Each process represents an outlet for making a beverage.

        :param beverage: Name of beverage to be made
        :return: None
        """
        ingredients = self.beverages.get(beverage)

        for ingredient in ingredients:  # Phase 1, checking if all ingredients exist
            if ingredient not in self.total_ingredients_quantity:
                print(f'{beverage} cannot be prepared because {ingredient} is not available')
                return

        for ingredient in ingredients:  # Phase 2, checking if each ingredient has sufficient quantity
            # Since this process will run concurrently with other processes, locking down the ingredient
            self.ingredients_lock[f'{ingredient}_lock'].acquire()

            updated_ingredient_quantity = self.total_ingredients_quantity[ingredient].value - ingredients[ingredient]
            if updated_ingredient_quantity < 0:  # This means order cant be processed since insufficient ingredients

                # If ingredients are not sufficient, updating low ingredient info
                self.update_ingredient_low_indicator(ingredient, self.total_ingredients_quantity[ingredient].value)

                # Alerting which beverages cannot be prepared
                print(f'{beverage} cannot be prepared because {ingredient} is not sufficient')

                self._release_locks()
                return

        for ingredient in ingredients:  # Phase 3, updating the quantity of respective ingredients
            updated_quantity = self.total_ingredients_quantity[ingredient].value - ingredients[ingredient]
            self.total_ingredients_quantity[ingredient].value = updated_quantity

            if self.total_ingredients_quantity[ingredient].value == 0:
                self.update_ingredient_low_indicator(ingredient, 0)

        print(f'{beverage} is prepared')
        self._release_locks()


def take_order(order_data):
    """
    Global method to initialize CoffeeShop class and take orders.
    :param order_data: dict containing order data
    :return: None
    """
    if order_data in [{}, None, '']:
        raise Exception("Input data is blank")

    orders = []

    coffee_shop = CoffeeShop(
            total_ingredients_quantity=order_data['machine']['total_items_quantity'],
            beverages=order_data['machine']['beverages']
        )
    for order in coffee_shop.beverages:
        process = Process(target=coffee_shop.process_order, args=(order,))
        orders.append(process)
        process.start()

    # Complete all the concurrent orders
    for order in orders:
        order.join()


if __name__ == '__main__':
    take_order(ORDER_DATA)
