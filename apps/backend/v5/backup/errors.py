class BackupError(Exception):
    pass


class BackupNotFoundError(BackupError):
    pass


class BackupInProgressError(BackupError):
    pass


class RestoreValidationError(BackupError):
    pass


class CloneError(BackupError):
    pass


class RetentionExpiredError(BackupError):
    pass


class LifecycleStateError(BackupError):
    pass
