def get_max_length(choices):
    """Вычисляет максимальную длину значений из списка choices."""
    return max(len(str(choice[0])) for choice in choices) if choices else 1
