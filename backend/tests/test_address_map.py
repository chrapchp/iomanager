###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

import math
import pytest
from app.models.address_map import AddressMap
from app.models.tag import DataType


@pytest.fixture
def am() -> AddressMap:
    return AddressMap()


# ---------------------------------------------------------------------------
# Basic allocation
# ---------------------------------------------------------------------------

class TestAllocateBasic:
    def test_bool_allocates_at_pool_start(self, am):
        assert am.allocate(DataType.BOOL, 1000) == 1000

    def test_int16_allocates_at_pool_start(self, am):
        assert am.allocate(DataType.INT16, 1400) == 1400

    def test_uint16_allocates_at_pool_start(self, am):
        assert am.allocate(DataType.UINT16, 3700) == 3700

    def test_byte_allocates_at_pool_start(self, am):
        assert am.allocate(DataType.BYTE, 500) == 500

    def test_sequential_bool_increments_by_one(self, am):
        first = am.allocate(DataType.BOOL, 1000)
        second = am.allocate(DataType.BOOL, 1000)
        assert second == first + 1

    def test_sequential_int16_increments_by_one(self, am):
        first = am.allocate(DataType.INT16, 1400)
        second = am.allocate(DataType.INT16, 1400)
        assert second == first + 1


# ---------------------------------------------------------------------------
# Even-boundary alignment (FLOAT, INT32, UINT32)
# ---------------------------------------------------------------------------

class TestEvenBoundary:
    @pytest.mark.parametrize("dtype", [DataType.FLOAT, DataType.INT32, DataType.UINT32])
    def test_allocates_on_even_boundary_when_start_is_even(self, am, dtype):
        addr = am.allocate(dtype, 3024)
        assert addr == 3024
        assert addr % 2 == 0

    @pytest.mark.parametrize("dtype", [DataType.FLOAT, DataType.INT32, DataType.UINT32])
    def test_allocates_on_next_even_when_start_is_odd(self, am, dtype):
        addr = am.allocate(dtype, 3025)
        assert addr == 3026
        assert addr % 2 == 0

    @pytest.mark.parametrize("dtype", [DataType.FLOAT, DataType.INT32, DataType.UINT32])
    def test_consumes_two_registers(self, am, dtype):
        addr = am.allocate(dtype, 3024)
        assert am.is_occupied(DataType.INT16, addr)
        assert am.is_occupied(DataType.INT16, addr + 1)
        assert not am.is_occupied(DataType.INT16, addr + 2)

    @pytest.mark.parametrize("dtype", [DataType.FLOAT, DataType.INT32, DataType.UINT32])
    def test_sequential_two_word_types_increment_by_two(self, am, dtype):
        first = am.allocate(dtype, 3024)
        second = am.allocate(dtype, 3024)
        assert second == first + 2

    def test_float_skips_odd_address_even_if_free(self, am):
        # Force first available even to be 3026 by occupying 3024/3025
        am.mark_occupied(DataType.INT16, 3024)
        am.mark_occupied(DataType.INT16, 3025)
        addr = am.allocate(DataType.FLOAT, 3024)
        assert addr == 3026


# ---------------------------------------------------------------------------
# Coil vs register address space independence
# ---------------------------------------------------------------------------

class TestAddressSpaceIsolation:
    def test_bool_and_int16_at_same_numeric_address_do_not_conflict(self, am):
        coil_addr = am.allocate(DataType.BOOL, 1000)
        reg_addr = am.allocate(DataType.INT16, 1000)
        assert coil_addr == 1000
        assert reg_addr == 1000

    def test_bool_does_not_affect_register_space(self, am):
        am.allocate(DataType.BOOL, 0)
        am.allocate(DataType.BOOL, 1)
        reg_addr = am.allocate(DataType.INT16, 0)
        assert reg_addr == 0

    def test_float_does_not_affect_coil_space(self, am):
        am.allocate(DataType.FLOAT, 0)
        coil_addr = am.allocate(DataType.BOOL, 0)
        assert coil_addr == 0


# ---------------------------------------------------------------------------
# mark_occupied
# ---------------------------------------------------------------------------

class TestMarkOccupied:
    def test_mark_bool_occupies_single_coil(self, am):
        am.mark_occupied(DataType.BOOL, 1000)
        assert 1000 in am.coil
        assert 1001 not in am.coil

    def test_mark_float_occupies_two_registers(self, am):
        am.mark_occupied(DataType.FLOAT, 3024)
        assert 3024 in am.register
        assert 3025 in am.register
        assert 3026 not in am.register

    def test_mark_occupied_blocks_subsequent_allocation(self, am):
        am.mark_occupied(DataType.INT16, 1400)
        addr = am.allocate(DataType.INT16, 1400)
        assert addr == 1401

    def test_mark_occupied_float_blocks_both_registers(self, am):
        am.mark_occupied(DataType.FLOAT, 3024)
        addr = am.allocate(DataType.FLOAT, 3024)
        assert addr == 3026


# ---------------------------------------------------------------------------
# TEXT size override
# ---------------------------------------------------------------------------

class TestTextSizeOverride:
    def test_text_allocates_ceil_texttagsize_div_2_registers(self, am):
        text_tag_size = 246
        size = math.ceil(text_tag_size / 2)
        addr = am.allocate(DataType.TEXT, 10, size_override=size)
        assert addr == 10
        # All consumed registers marked occupied
        for i in range(size):
            assert am.is_occupied(DataType.INT16, 10 + i)
        # Next register is free
        assert not am.is_occupied(DataType.INT16, 10 + size)

    def test_text_size_override_respected_in_sequential_allocation(self, am):
        size = math.ceil(246 / 2)
        first = am.allocate(DataType.TEXT, 10, size_override=size)
        second = am.allocate(DataType.INT16, 10)
        assert second == first + size


# ---------------------------------------------------------------------------
# is_occupied
# ---------------------------------------------------------------------------

class TestIsOccupied:
    def test_free_address_is_not_occupied(self, am):
        assert not am.is_occupied(DataType.BOOL, 1000)
        assert not am.is_occupied(DataType.INT16, 1400)

    def test_allocated_address_is_occupied(self, am):
        am.allocate(DataType.BOOL, 1000)
        assert am.is_occupied(DataType.BOOL, 1000)

    def test_float_second_register_is_occupied(self, am):
        am.allocate(DataType.FLOAT, 3024)
        assert am.is_occupied(DataType.INT16, 3025)
