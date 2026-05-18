class QuotaExceededError(Exception):
    def __init__(self, quota_type: str, current: int, max_value: int, message: str):
        self.quota_type = quota_type
        self.current = current
        self.max_value = max_value
        self.message = message
        super().__init__(message)
