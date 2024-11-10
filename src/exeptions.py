class InsufficientDataError(Exception):
    def __init__(self) -> None:
        super().__init__("Not sufficient data available")
