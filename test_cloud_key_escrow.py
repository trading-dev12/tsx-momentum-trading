import json

import pytest
from cryptography.fernet import Fernet

from utilities.cloud_key_escrow import (
    create_recovery_bundle,
    recover_key_from_bundle,
)


PASSPHRASE = (
    "northstar test recovery phrase"
)


def test_recovery_bundle_round_trip(
    tmp_path,
):
    key_path = (
        tmp_path / "cloud_backup.key"
    )

    bundle_path = (
        tmp_path / "recovery.enc.json"
    )

    original = Fernet.generate_key()

    key_path.write_bytes(
        original
    )

    result = create_recovery_bundle(
        key_path,
        bundle_path,
        PASSPHRASE,
    )

    recovered = (
        recover_key_from_bundle(
            bundle_path,
            PASSPHRASE,
        )
    )

    assert result["success"] is True
    assert result["verified"] is True
    assert recovered == original


def test_raw_key_not_stored_in_bundle(
    tmp_path,
):
    key_path = (
        tmp_path / "cloud_backup.key"
    )

    bundle_path = (
        tmp_path / "recovery.enc.json"
    )

    original = Fernet.generate_key()

    key_path.write_bytes(
        original
    )

    create_recovery_bundle(
        key_path,
        bundle_path,
        PASSPHRASE,
    )

    bundle_bytes = (
        bundle_path.read_bytes()
    )

    assert (
        original
        not in bundle_bytes
    )


def test_wrong_passphrase_fails(
    tmp_path,
):
    key_path = (
        tmp_path / "cloud_backup.key"
    )

    bundle_path = (
        tmp_path / "recovery.enc.json"
    )

    key_path.write_bytes(
        Fernet.generate_key()
    )

    create_recovery_bundle(
        key_path,
        bundle_path,
        PASSPHRASE,
    )

    with pytest.raises(
        ValueError,
        match="Incorrect recovery passphrase",
    ):
        recover_key_from_bundle(
            bundle_path,
            "this is definitely the wrong phrase",
        )


def test_recovered_key_can_be_written(
    tmp_path,
):
    key_path = (
        tmp_path / "cloud_backup.key"
    )

    bundle_path = (
        tmp_path / "recovery.enc.json"
    )

    restored_path = (
        tmp_path
        / "restored"
        / "cloud_backup.key"
    )

    original = Fernet.generate_key()

    key_path.write_bytes(
        original
    )

    create_recovery_bundle(
        key_path,
        bundle_path,
        PASSPHRASE,
    )

    recover_key_from_bundle(
        bundle_path,
        PASSPHRASE,
        output_path=restored_path,
    )

    assert restored_path.read_bytes() == original
