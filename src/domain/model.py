import typing as t
from datetime import date
from dataclasses import dataclass

from src.domain.exceptions import OutOfStock


@dataclass(frozen=True)
class OrderLine:
    order_id: str
    sku: str  # stock keeping unit
    qty: int


class Batch:
    def __init__(
        self, ref:  str,  sku: str, qty: int, eta: t.Optional[date]   
    ):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations: t.Set[OrderLine] = set()
    
    def allocate(self,  line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        return hash(self.reference)


def allocate(line: OrderLine, batches: t.List[Batch]) -> str:
    try:
        batch = next(
        b for b in sorted(batches) if b.can_allocate(line)
        )
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f'{line.sku} does not exist')