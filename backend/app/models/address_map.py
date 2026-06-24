###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

from __future__ import annotations
from dataclasses import dataclass, field
from app.models.tag import DataType


@dataclass
class AddressMap:
    """Tracks occupied Modbus addresses, separated by address space."""
    coil: set[int] = field(default_factory=set)
    register: set[int] = field(default_factory=set)

    def _size(self, data_type: DataType, size_override: int | None) -> int:
        """Resolve register size, allowing caller to override for TEXT tags."""
        return size_override if size_override is not None else data_type.register_size

    def mark_occupied(
        self, data_type: DataType, address: int, size_override: int | None = None
    ) -> None:
        size = self._size(data_type, size_override)
        if data_type.is_digital:
            self.coil.add(address)
        else:
            for i in range(size):
                self.register.add(address + i)

    def allocate(
        self, data_type: DataType, pool_start: int, size_override: int | None = None
    ) -> int:
        """
        Find the next free address at or above pool_start.
        FLOAT/32BIT types are aligned to even boundaries.
        Pass size_override for TEXT tags (ceil(TextTagSize / 2) registers).
        Raises RuntimeError if no address can be found within a safe limit.
        """
        occupied = self.coil if data_type.is_digital else self.register
        size = self._size(data_type, size_override)
        addr = pool_start

        for _ in range(65536):
            if data_type.requires_even_boundary and addr % 2 != 0:
                addr += 1
                continue
            slots = set(range(addr, addr + size))
            if not slots & occupied:
                for i in range(size):
                    occupied.add(addr + i)
                return addr
            addr += 1

        raise RuntimeError(
            f"No free address found for {data_type} starting from {pool_start}"
        )

    def is_occupied(
        self, data_type: DataType, address: int, size_override: int | None = None
    ) -> bool:
        occupied = self.coil if data_type.is_digital else self.register
        size = self._size(data_type, size_override)
        return any((address + i) in occupied for i in range(size))
