"""Tests for Module 7: Cryptographic Hashing and Merkle Tree."""

import hashlib
import io
from pathlib import Path
import pytest

from dbguard.hashing.file_hash import compute_file_sha256
from dbguard.hashing.stream_hash import StreamHasher
from dbguard.hashing.chunk_hash import ChunkHasher
from dbguard.hashing.merkle import MerkleTree, verify_merkle_proof


def test_compressed_file_hash(tmp_path: Path):
    """Test 13: Correct chunked SHA-256 calculation for compressed file."""
    content = b"Exact compressed binary test payload \x00\xff\x10\x20" * 1000
    file_path = tmp_path / "test_comp.bin"
    file_path.write_bytes(content)

    expected_sha = hashlib.sha256(content).hexdigest()
    calculated_sha = compute_file_sha256(file_path, chunk_size=256)
    assert calculated_sha == expected_sha


def test_decompressed_stream_hash():
    """Test 14: Correct incremental SHA-256 for decompressed chunks."""
    chunks = [b"Chunk1_", b"Chunk2_", b"Chunk3_Final"]
    combined = b"".join(chunks)

    hasher = StreamHasher()
    for ch in chunks:
        hasher.update(ch)

    expected_sha = hashlib.sha256(combined).hexdigest()
    assert hasher.hexdigest() == expected_sha


def test_chunk_hashes():
    """Test 15: Exact boundary chunk hashing."""
    chunk_size = 100
    data = b"x" * 250  # Should yield 2 full 100B chunks + 1 50B chunk

    chunk_hasher = ChunkHasher(chunk_boundary_bytes=chunk_size)
    chunk_hasher.update(data[:120])
    chunk_hasher.update(data[120:])
    entries = chunk_hasher.finalize()

    assert len(entries) == 3
    assert entries[0].length_bytes == 100
    assert entries[0].start_byte == 0
    assert entries[0].end_byte == 100
    assert entries[0].sha256 == hashlib.sha256(b"x" * 100).hexdigest()

    assert entries[1].length_bytes == 100
    assert entries[1].start_byte == 100
    assert entries[1].end_byte == 200

    assert entries[2].length_bytes == 50
    assert entries[2].start_byte == 200
    assert entries[2].end_byte == 250
    assert entries[2].sha256 == hashlib.sha256(b"x" * 50).hexdigest()


def test_merkle_tree_proofs_and_odd_nodes():
    """Test Merkle tree with 1 leaf, 3 leaves (odd), audit path generation, and tampered detection."""
    # 1. Single leaf
    tree_1 = MerkleTree([b"Leaf0"])
    assert len(tree_1.root_hex) == 64

    # 2. Three leaves (odd count tests node promotion)
    leaves = [b"LeafA", b"LeafB", b"LeafC"]
    tree_3 = MerkleTree(leaves)
    assert len(tree_3.root_hex) == 64

    # Verify proof for each leaf
    for i in range(len(leaves)):
        proof = tree_3.generate_proof(i)
        is_valid = verify_merkle_proof(leaves[i], i, proof, tree_3.root_hex)
        assert is_valid is True

    # Altered leaf fails verification
    proof_0 = tree_3.generate_proof(0)
    assert verify_merkle_proof(b"TAMPERED_LEAF", 0, proof_0, tree_3.root_hex) is False

