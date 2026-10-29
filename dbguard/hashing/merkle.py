"""Cryptographic Merkle Tree construction and proof verification.

Implements domain-separated leaf (0x00) and internal node (0x01) hashing
following RFC 6962 principles to prevent second-preimage attacks.
"""

import hashlib
from typing import List, Tuple, Optional


def hash_leaf(data: bytes) -> bytes:
    """Compute domain-separated leaf hash: SHA-256(0x00 || data)."""
    return hashlib.sha256(b"\x00" + data).digest()


def hash_internal(left: bytes, right: bytes) -> bytes:
    """Compute domain-separated internal node hash: SHA-256(0x01 || left || right)."""
    return hashlib.sha256(b"\x01" + left + right).digest()


class MerkleTree:
    """Merkle tree over chunk digests or raw data elements."""

    def __init__(self, leaf_data_or_hashes: List[bytes], are_already_leaf_hashed: bool = False):
        if are_already_leaf_hashed:
            self.leaves: List[bytes] = list(leaf_data_or_hashes)
        else:
            self.leaves: List[bytes] = [hash_leaf(item) for item in leaf_data_or_hashes]

        self.levels: List[List[bytes]] = []
        self._build_tree()

    def _build_tree(self) -> None:
        """Construct levels bottom-up. Unpaired odd nodes are promoted to the next level."""
        if not self.leaves:
            self.levels = [[]]
            return

        current_level = self.leaves
        self.levels.append(current_level)

        while len(current_level) > 1:
            next_level: List[bytes] = []
            i = 0
            while i < len(current_level):
                left = current_level[i]
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                    parent = hash_internal(left, right)
                    next_level.append(parent)
                    i += 2
                else:
                    # Unpaired odd node: promote directly to next layer
                    next_level.append(left)
                    i += 1
            self.levels.append(next_level)
            current_level = next_level

    @property
    def root_hex(self) -> str:
        """Root hash in hex string representation."""
        if not self.leaves or not self.levels or not self.levels[-1]:
            return ""
        return self.levels[-1][0].hex()

    def generate_proof(self, leaf_index: int) -> List[Tuple[str, str]]:
        """Generate audit path proof for the leaf at leaf_index.

        Returns:
            List of (sibling_hex_hash, direction) where direction is 'left' or 'right'.
        """
        if leaf_index < 0 or leaf_index >= len(self.leaves):
            raise IndexError(f"Leaf index {leaf_index} out of bounds (0..{len(self.leaves)-1})")

        proof: List[Tuple[str, str]] = []
        idx = leaf_index

        for level in self.levels[:-1]:
            if idx % 2 == 0:
                # We are left child; sibling is right child
                if idx + 1 < len(level):
                    proof.append((level[idx + 1].hex(), "right"))
            else:
                # We are right child; sibling is left child
                proof.append((level[idx - 1].hex(), "left"))
            idx //= 2

        return proof


def verify_merkle_proof(
    leaf_bytes: bytes,
    leaf_index: int,
    proof: List[Tuple[str, str]],
    expected_root_hex: str,
    is_prehashed_leaf: bool = False
) -> bool:
    """Verify that a given leaf belongs to the tree with expected_root_hex.

    Args:
        leaf_bytes: Raw leaf bytes or precomputed leaf hash.
        leaf_index: Original index of the leaf.
        proof: Sibling path from generate_proof.
        expected_root_hex: Expected Merkle root hex string.
        is_prehashed_leaf: Whether leaf_bytes is already the domain-separated leaf hash.

    Returns:
        True if the proof reconstructs the exact root hash; False otherwise.
    """
    current = leaf_bytes if is_prehashed_leaf else hash_leaf(leaf_bytes)

    for sibling_hex, direction in proof:
        sibling = bytes.fromhex(sibling_hex)
        if direction == "right":
            current = hash_internal(current, sibling)
        else:
            current = hash_internal(sibling, current)

    return current.hex() == expected_root_hex

