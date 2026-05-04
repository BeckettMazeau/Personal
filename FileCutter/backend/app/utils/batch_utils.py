from typing import List, TypeVar, Iterator

T = TypeVar('T')

def batch_items(items: List[T], batch_size: int = 20) -> Iterator[List[T]]:
    """
    Yield successive batches of a specified size from a list of items.

    Args:
        items: The list of items to be batched.
        batch_size: The size of each batch. Defaults to 20.

    Yields:
        A list containing a batch of items.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0")

    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]
