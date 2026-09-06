"""Stable product quality flags shared by every LS4T level."""

from __future__ import annotations

from enum import IntFlag

import numpy as np


class QualityFlag(IntFlag):
    GOOD = 0
    INPUT_INVALID = 1 << 0
    CLOUD = 1 << 1
    OUT_OF_RANGE = 1 << 2
    RETRIEVAL_FAILED = 1 << 3
    ILL_CONDITIONED = 1 << 4
    NORMALIZATION_FAILED = 1 << 5
    PROFILE_MISMATCH = 1 << 6
    FUSION_REJECTED = 1 << 7
    LOW_SUPPORT = 1 << 8


INVALID_FLAGS = (
    QualityFlag.INPUT_INVALID
    | QualityFlag.CLOUD
    | QualityFlag.OUT_OF_RANGE
    | QualityFlag.RETRIEVAL_FAILED
    | QualityFlag.NORMALIZATION_FAILED
    | QualityFlag.PROFILE_MISMATCH
    | QualityFlag.LOW_SUPPORT
)


def new_flags(shape: tuple[int, ...]) -> np.ndarray:
    return np.zeros(shape, dtype=np.uint16)


def set_flag(flags: np.ndarray, mask: np.ndarray, flag: QualityFlag) -> None:
    flags[np.asarray(mask, dtype=bool)] |= np.uint16(flag)


def usable(flags: np.ndarray, reject: QualityFlag = INVALID_FLAGS) -> np.ndarray:
    return (np.asarray(flags, dtype=np.uint16) & np.uint16(reject)) == 0
