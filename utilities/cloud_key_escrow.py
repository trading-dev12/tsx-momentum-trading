import base64
import getpass
import json
import os
from pathlib import Path

from cryptography.fernet import (
    Fernet,
    InvalidToken,
)
from cryptography.hazmat.primitives.kdf.scrypt import (
    Scrypt,
)

from utilities.backup_manager import (
    PROJECT_ROOT,
    load_local_backup_settings,
    resolve_backup_root,
)


CLOUD_KEY_FILE = (
    PROJECT_ROOT
    / "config"
    / "cloud_backup.key"
)

RECOVERY_BUNDLE_NAME = (
    "Northstar_Recovery_Key.enc.json"
)

SCRYPT_N = 2 ** 15
SCRYPT_R = 8
SCRYPT_P = 1


def _derive_wrapping_key(
    passphrase,
    salt,
    n=SCRYPT_N,
    r=SCRYPT_R,
    p=SCRYPT_P,
):
    if not isinstance(
        passphrase,
        str,
    ):
        raise TypeError(
            "Recovery passphrase must be text."
        )

    if len(passphrase) < 16:
        raise ValueError(
            "Recovery passphrase must contain "
            "at least 16 characters."
        )

    kdf = Scrypt(
        salt=salt,
        length=32,
        n=n,
        r=r,
        p=p,
    )

    derived = kdf.derive(
        passphrase.encode("utf-8")
    )

    return base64.urlsafe_b64encode(
        derived
    )


def create_recovery_bundle(
    key_path,
    bundle_path,
    passphrase,
):
    key_path = Path(key_path)
    bundle_path = Path(bundle_path)

    if not key_path.is_file():
        raise FileNotFoundError(
            "Northstar cloud encryption key "
            "was not found."
        )

    raw_key = key_path.read_bytes()

    # Validate that it really is a Fernet key.
    Fernet(raw_key)

    salt = os.urandom(16)

    wrapping_key = (
        _derive_wrapping_key(
            passphrase,
            salt,
        )
    )

    encrypted_key = Fernet(
        wrapping_key
    ).encrypt(
        raw_key
    )

    payload = {
        "format":
            "NORTHSTAR_RECOVERY_KEY",
        "version": 1,
        "kdf": "scrypt",
        "n": SCRYPT_N,
        "r": SCRYPT_R,
        "p": SCRYPT_P,
        "salt":
            base64.b64encode(
                salt
            ).decode("ascii"),
        "encrypted_key":
            encrypted_key.decode(
                "ascii"
            ),
    }

    bundle_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = (
        bundle_path.with_suffix(
            bundle_path.suffix + ".tmp"
        )
    )

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary.replace(
        bundle_path
    )

    # Immediately prove the bundle can recover
    # exactly the original key.
    recovered = recover_key_from_bundle(
        bundle_path,
        passphrase,
    )

    if recovered != raw_key:
        raise RuntimeError(
            "Recovery-key verification failed."
        )

    return {
        "success": True,
        "bundle_path":
            str(bundle_path),
        "verified": True,
    }


def recover_key_from_bundle(
    bundle_path,
    passphrase,
    output_path=None,
):
    bundle_path = Path(
        bundle_path
    )

    payload = json.loads(
        bundle_path.read_text(
            encoding="utf-8-sig"
        )
    )

    if (
        payload.get("format")
        != "NORTHSTAR_RECOVERY_KEY"
    ):
        raise ValueError(
            "Not a Northstar recovery-key bundle."
        )

    salt = base64.b64decode(
        payload["salt"]
    )

    wrapping_key = (
        _derive_wrapping_key(
            passphrase,
            salt,
            n=int(payload["n"]),
            r=int(payload["r"]),
            p=int(payload["p"]),
        )
    )

    try:
        raw_key = Fernet(
            wrapping_key
        ).decrypt(
            payload[
                "encrypted_key"
            ].encode("ascii")
        )
    except InvalidToken as exc:
        raise ValueError(
            "Incorrect recovery passphrase "
            "or damaged recovery bundle."
        ) from exc

    # Validate the recovered key.
    Fernet(raw_key)

    if output_path is not None:
        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = (
            output_path.with_suffix(
                output_path.suffix + ".tmp"
            )
        )

        temporary.write_bytes(
            raw_key
        )

        temporary.replace(
            output_path
        )

    return raw_key


def get_recovery_bundle_path():
    settings = (
        load_local_backup_settings()
    )

    cloud_root_value = (
        settings.get(
            "cloud_backup_root"
        )
    )

    if not cloud_root_value:
        raise RuntimeError(
            "cloud_backup_root is not configured."
        )

    cloud_root = resolve_backup_root(
        cloud_root_value
    )

    return (
        cloud_root
        / RECOVERY_BUNDLE_NAME
    )


def main():
    print(
        "NORTHSTAR CLOUD RECOVERY KEY"
    )

    print(
        "\nYour passphrase is NOT displayed "
        "and is NOT stored by Northstar."
    )

    print(
        "Use a long phrase you can recover "
        "during a complete PC failure.\n"
    )

    first = getpass.getpass(
        "Recovery passphrase: "
    )

    second = getpass.getpass(
        "Confirm passphrase: "
    )

    if first != second:
        raise SystemExit(
            "ERROR: passphrases did not match."
        )

    try:
        result = create_recovery_bundle(
            CLOUD_KEY_FILE,
            get_recovery_bundle_path(),
            first,
        )

    except Exception as exc:
        raise SystemExit(
            f"ERROR: {exc}"
        )

    print(
        "\nPASS - encrypted recovery key created"
    )

    print(
        "PASS - recovery key decrypted "
        "and verified"
    )

    print(
        "Bundle:",
        result["bundle_path"],
    )

    print(
        "\nThe raw encryption key was NOT "
        "copied to OneDrive."
    )


if __name__ == "__main__":
    main()
