def doc(docstring):
    """Декоратор для динамической подстановки значений в докстринг."""
    def decorator(func):
        func.__doc__ = docstring
        return func
    return decorator
