import pytest
from app.utils.batch_utils import batch_items

def test_batch_items():
    items = list(range(50))
    batches = list(batch_items(items, batch_size=20))

    assert len(batches) == 3
    assert len(batches[0]) == 20
    assert len(batches[1]) == 20
    assert len(batches[2]) == 10

    assert batches[0] == list(range(0, 20))
    assert batches[1] == list(range(20, 40))
    assert batches[2] == list(range(40, 50))

def test_batch_items_invalid_size():
    items = [1, 2, 3]
    with pytest.raises(ValueError):
        list(batch_items(items, batch_size=0))
