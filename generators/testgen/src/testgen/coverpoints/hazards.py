##################################
# hazards.py
#
# jcarlin@hmc.edu Oct 2025
# SPDX-License-Identifier: Apache-2.0
##################################

"""Hazard coverpoint generators (cp_gpr_hazard, cp_fpr_hazard)."""

from __future__ import annotations

from testgen.asm.helpers import write_sigupd
from testgen.coverpoints.registry import add_coverpoint_generator
from testgen.data.params import InstructionParams
from testgen.data.state import TestData
from testgen.data.test_chunk import TestChunk
from testgen.formatters import format_instruction
from testgen.formatters.params import generate_random_params
from testgen.formatters.registry import get_instr_type_config


def _hazard_class(coverpoint: str) -> str:
    """Return the requested hazard class suffix: r, w, or rw."""
    parts = coverpoint.split("_")
    if len(parts) > 3 and parts[-1] in {"r", "w", "rw"}:
        return parts[-1]
    return "rw"


def _int_sources(instr_type: str) -> list[str]:
    if instr_type == "S":
        # Store formatters move the signature pointer into rs1 for checking.
        # Keep hazard tests on store data so the register allocator state stays coherent.
        return ["rs2"]
    required = get_instr_type_config(instr_type).required_params or set()
    return [field for field in ("rs1", "rs2", "rs3") if field in required]


def _float_sources(instr_type: str) -> list[str]:
    required = get_instr_type_config(instr_type).required_params or set()
    return [field for field in ("fs1", "fs2", "fs3") if field in required]


def _has_int_dest(instr_type: str) -> bool:
    required = get_instr_type_config(instr_type).required_params or set()
    return "rd" in required


def _has_float_dest(instr_type: str) -> bool:
    required = get_instr_type_config(instr_type).required_params or set()
    return "fd" in required


def _get_param(params: InstructionParams, field: str) -> int:
    value = getattr(params, field)
    assert value is not None
    return value


def _generate_with_fixed_int_source(test_data: TestData, instr_type: str, field: str, reg: int) -> InstructionParams:
    if field == "rs1":
        return generate_random_params(test_data, instr_type, rs1=reg)
    if field == "rs2":
        return generate_random_params(test_data, instr_type, rs2=reg)
    if field == "rs3":
        return generate_random_params(test_data, instr_type, rs3=reg)
    raise ValueError(f"Unknown integer source field: {field}")


def _generate_with_fixed_float_source(test_data: TestData, instr_type: str, field: str, reg: int) -> InstructionParams:
    if field == "fs1":
        return generate_random_params(test_data, instr_type, fs1=reg)
    if field == "fs2":
        return generate_random_params(test_data, instr_type, fs2=reg)
    if field == "fs3":
        return generate_random_params(test_data, instr_type, fs3=reg)
    raise ValueError(f"Unknown floating-point source field: {field}")


def _make_gpr_hazard(
    instr_name: str,
    instr_type: str,
    coverpoint: str,
    test_data: TestData,
    haz_type: str,
    field: str | None,
    case_idx: int,
    filler: str = "",
) -> list[str]:
    """Generate one adjacent GPR producer/consumer hazard testcase."""
    producer = generate_random_params(test_data, "R", exclude_regs=[0, 1, 2, 4, 5, 7, 8, 12, 13])
    assert producer.rd is not None and producer.rs1 is not None and producer.rs2 is not None

    if haz_type == "raw":
        assert field is not None
        consumer = _generate_with_fixed_int_source(test_data, instr_type, field, producer.rd)

        # Address-based consumers need the producer to preserve the computed base
        # register that their formatter establishes during setup.
        if field == "rs1" and instr_type in {"L", "S", "JR"}:
            test_data.int_regs.return_registers([producer.rs1, producer.rs2])
            producer.rs1 = producer.rd
            producer.rs2 = 0
    elif haz_type == "waw":
        consumer = generate_random_params(test_data, instr_type, rd=producer.rd)
    elif haz_type == "war":
        assert field is not None
        consumer = generate_random_params(test_data, instr_type, rd=_get_param(producer, field))
    elif haz_type == "nohaz":
        consumer = generate_random_params(test_data, instr_type)
    else:
        raise ValueError(f"Unknown hazard type: {haz_type}")

    bin_name = haz_type if field is None else f"{haz_type}_{field}_{case_idx}"
    label_line = test_data.add_testcase(bin_name, coverpoint)
    setup1, test1, check1 = format_instruction("add", "R", test_data, producer)
    if instr_type == "S":
        assert test_data.test_chunk is not None
        test_data.test_chunk.sigupd_count -= 1
        check1 = ""
    setup2, test2, check2 = format_instruction(instr_name, instr_type, test_data, consumer)
    if instr_type == "S" and haz_type != "waw":
        check1 = write_sigupd(producer.rd, test_data, "int")

    mid = ["  " + filler] if filler else []
    lines = [f"\n# Testcase {coverpoint} {bin_name}", setup1, setup2, label_line, test1, *mid, test2]
    if haz_type == "waw":
        lines.append(check2)
    elif instr_type == "S":
        if check2:
            lines.append(check2)
        if check1:
            lines.append(check1)
    else:
        if check1:
            lines.append(check1)
        if check2:
            lines.append(check2)

    test_data.int_regs.return_registers(producer.used_int_regs)
    test_data.int_regs.return_registers(consumer.used_int_regs)
    test_data.float_regs.return_registers(consumer.used_float_regs)
    return [line for line in lines if line]


def _make_fpr_hazard(
    instr_name: str,
    instr_type: str,
    coverpoint: str,
    test_data: TestData,
    haz_type: str,
    field: str | None,
    case_idx: int,
    filler: str = "",
) -> list[str]:
    """Generate one adjacent FPR producer/consumer hazard testcase."""
    producer = generate_random_params(test_data, "FR", fp_load_type="single")
    assert producer.fd is not None and producer.fs1 is not None and producer.fs2 is not None

    if haz_type == "raw":
        assert field is not None
        consumer = _generate_with_fixed_float_source(test_data, instr_type, field, producer.fd)
    elif haz_type == "waw":
        consumer = generate_random_params(test_data, instr_type, fd=producer.fd)
    elif haz_type == "war":
        assert field is not None
        consumer = generate_random_params(test_data, instr_type, fd=_get_param(producer, field))
    elif haz_type == "nohaz":
        consumer = generate_random_params(test_data, instr_type)
    else:
        raise ValueError(f"Unknown hazard type: {haz_type}")

    bin_name = haz_type if field is None else f"{haz_type}_{field}_{case_idx}"
    label_line = test_data.add_testcase(bin_name, coverpoint)
    setup1, test1, check1 = format_instruction("fadd.s", "FR", test_data, producer)
    setup2, test2, check2 = format_instruction(instr_name, instr_type, test_data, consumer)

    mid = ["  " + filler] if filler else []
    lines = [f"\n# Testcase {coverpoint} {bin_name}", setup1, setup2, label_line, test1, *mid, test2]
    if haz_type == "waw":
        lines.append(check2)
    else:
        if check1:
            lines.append(check1)
        if check2:
            lines.append(check2)

    test_data.float_regs.return_registers(producer.used_float_regs)
    test_data.float_regs.return_registers(consumer.used_float_regs)
    test_data.int_regs.return_registers(consumer.used_int_regs)
    return [line for line in lines if line]


@add_coverpoint_generator("cp_gpr_hazard", "cp_fpr_hazard")
def make_cp_hazard(instr_name: str, instr_type: str, coverpoint: str, test_data: TestData) -> list[TestChunk]:
    """Generate adjacent RAW, WAW, WAR, and no-hazard register tests."""
    tc = test_data.begin_test_chunk()
    haz_class = _hazard_class(coverpoint)
    test_lines: list[str] = []

    if coverpoint.startswith("cp_fpr_hazard"):
        source_fields = _float_sources(instr_type)
        has_dest = _has_float_dest(instr_type)
        make_hazard = _make_fpr_hazard
    else:
        source_fields = _int_sources(instr_type)
        has_dest = _has_int_dest(instr_type)
        make_hazard = _make_gpr_hazard

    test_lines.extend(make_hazard(instr_name, instr_type, coverpoint, test_data, "nohaz", None, 0))

    FILLERS = [
        "addi x0, x0, 0",
        "add x6, x3, x9",
        "xor x6, x3, x9",
    ]
    if "r" in haz_class:
        for idx, field in enumerate(source_fields):
            for fidx, filler in enumerate(FILLERS):
                test_lines.extend(
                    make_hazard(
                        instr_name, instr_type, coverpoint, test_data, "raw", field, idx * len(FILLERS) + fidx, filler
                    )
                )

    if "w" in haz_class and has_dest:
        test_lines.extend(make_hazard(instr_name, instr_type, coverpoint, test_data, "waw", None, 0))
        for idx, field in enumerate(source_fields):
            test_lines.extend(make_hazard(instr_name, instr_type, coverpoint, test_data, "war", field, idx))

    tc.code = "\n".join(test_lines)
    return [test_data.end_test_chunk()]
