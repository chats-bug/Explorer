class MaxIterationsReached(Exception):
    def __init__(self, num_iters, message="Max iterations reached."):
        self.message = message
        self.num_iters = num_iters
        super().__init__(f"{self.message} (num_iters={self.num_iters})")
