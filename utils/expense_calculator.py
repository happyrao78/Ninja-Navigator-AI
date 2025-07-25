class Calculator:
    @staticmethod
    def multiply(a: int, b: int) -> int:
        
        return a * b
    
    @staticmethod
    def calculate_total(*x: float) -> float:

        return sum(x)
    
    @staticmethod
    def calculate_daily_budget(total: float, days: int) -> float:
        """
        Calculate daily budget

        Args:
            total (float): Total cost.
            days (int): Total number of days

        Returns:
            float: Expense for a single day
        """
        return total / days if days > 0 else 0
    