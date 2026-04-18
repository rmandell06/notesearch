class AppError(Exception):
    pass


class StorageError(AppError):
    pass


class NotFoundError(AppError):
    pass


class AuthError(AppError):
    pass


class EmbeddingError(AppError):
    pass


class TranscriptionError(AppError):
    pass
