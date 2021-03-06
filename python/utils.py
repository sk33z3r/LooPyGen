
from copyreg import clear_extension_cache
from dataclasses import dataclass
from typing import TypeVar, Generic
from collections import OrderedDict
from tempfile import TemporaryDirectory
from glob import glob
import subprocess
import json
import sys
import os
import re

@dataclass
class Struct(dict):
    def __init__(self, d: dict = None):
        if d:
            for k,v in d.items():
                super().__setitem__(k,v)
    def __getattr__(self, name):
        if super().__contains__(name):
            return super().__getitem__(name)
        else:
            return None
    def __setattr__(self, name, value):
        return super().__setitem__(name, value)
    def __delattr__(self, name):
        return super().__delitem__(name)
    def __str__(self):
        return super().__str__()
    def __repr__(self):
        return super().__repr__()

# Print exception type and traceback without leaking potentially sensitive information
def print_exception_secret():
    from traceback import print_tb
    from sys import exc_info
    print(type(exc_info()[0]))
    print_tb(exc_info()[2])

# Based off of the PHP implementation
def sanitize(string: str, force_lowercase: bool = True, alphanum_only: bool = False):
    strip = ["~", "`", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "=", "+", "[", "{", "]",
        "}", "\\", "|", ";", ":", "\"", "'", "&#8216;", "&#8217;", "&#8220;", "&#8221;", "&#8211;", "&#8212;",
        "â€”", "â€“", ",", "<", ".", ">", "/", "?"]

    clean = "".join(c for c in string if c not in strip)
    clean = clean.strip()
    clean = re.sub(r"\s+", "_", clean)
    clean = re.sub(r"[^a-zA-Z0-9]", "", clean) if alphanum_only else clean
    clean = clean.lower() if force_lowercase else clean
    return clean


def load_traits(name: str = None):
    TRAITS_VERSION = "v1.0.0"
    traits_path = ""
    if name:
        traits_path = os.path.join("./collections", name, "config", "traits.json")
    else:
        all_jsons = glob("./collections/*/config/traits.json")
        all_names = []
        for f in all_jsons:
            with open(f, 'r') as j:
                all_names.append(json.load(j).get("collection_name", "Unknown collection name"))
        assert len(all_names) > 0, "Found 0 existing collections in ./collections"

        print(f"Found {len(all_names)} collections:\n  " + "\n  ".join( [ f"{i+1}. {n}" for i,n in enumerate(all_names)] ))
        while True:
            print(f"Pick one (1~{len(all_names)}): ", end="")
            s = input().lower()
            try:
                s = int(s)
            except ValueError as err:
                continue
            if (s > 0) and (s <= len(all_names)):
                break
        traits_path = all_jsons[s - 1]

    with open(traits_path) as f:
        traits_json = json.load(f)

    # Convert version if needed
    if 'version' in traits_json and traits_json['version'] != TRAITS_VERSION:
        with TemporaryDirectory() as tempdir:
            converted_path = os.path.join(tempdir, 'traits_converted.json')
            ret_code = subprocess.call(f"python3 python/json-convert.py --file {traits_path} --version {TRAITS_VERSION} --output {converted_path}", shell=True)
            assert ret_code == 0, f"Could not convert {traits_path} to version {TRAITS_VERSION}"
            with open(converted_path, 'r') as f:
                traits_json = json.load(f)
    return Struct(traits_json)

def save_config_json(config: str, path: str, base64secret: str = None):
    from jose import jwe
    from base64 import b64decode
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    with open(config) as f:
        config_json = json.load(f)

    # Check for provided passphrase
    if base64secret is not None:

        # Decode passphrase
        try:
            secret = b64decode(base64secret)
        except Exception as err:
            print_exception_secret()
            sys.exit(f"Unable to decode provided passphrase")

        # Derive key
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390000,
        )
        try:
            key = kdf.derive(secret)
        except Exception as err:
            print_exception_secret()
            sys.exit(f"Unable to derive key from provided passphrase")

        # Encrypt
        try:
            cypher = jwe.encrypt(json.dumps(config_json), key, algorithm="dir", encryption="A256GCM")
        except Exception as err:
            print_exception_secret()
            sys.exit(f"Unable to encrypt config")
        enc_config = {
            "cypher": cypher.decode("utf-8"),
            "salt": "0x" + salt.hex()
        }

        # write encrypted config to file
        file = open(path, 'w')
        file.write(json.dumps(enc_config))
        file.close()

        # Return true or false result
        if os.path.exists(path):
            return True
        else:
            return False

    else:
        sys.exit("Unable to encrypt config: No passphrase provided")

# Load a config.json file from disk and decrypts it if needed (passphrase from provided base64secret, or asking the user for it)
def load_config_json(path: str, base64secret: str = None, disallow_prompt: bool = False):
    if not os.path.exists(path):
        sys.exit(f"Unable to load {path}: Config file not found. Did you create it? If not, go to http://localhost:8080/")

    with open(path) as f:
        config_json = json.load(f)

    # Check for encryption
    if 'cypher' in config_json:
        from jose import jwe
        from base64 import b64decode
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        enc_config = config_json
        salt = bytes.fromhex(enc_config['salt'].replace("0x", ""))

        # Check for provided passphrase
        if base64secret is not None:
            try:    # Decrypt
                try:
                    secret = b64decode(base64secret)
                except Exception as err:
                    print_exception_secret()
                    sys.exit(f"Unable to decode provided passphrase")
                kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
                try:
                    key = kdf.derive(secret)
                except Exception as err:
                    print_exception_secret()
                    sys.exit(f"Unable to derive key from provided passphrase")

                cypher = enc_config['cypher'].encode('utf-8')
                try:
                    config_json = json.loads(jwe.decrypt(cypher, key))
                except Exception as err:
                    print_exception_secret()
                    sys.exit(f"Unable to decrypt config")
            except jwe.JWEError as err:
                sys.exit(f"Unable to load {path}: Invalid config passphrase provided")
        # Error out if --noprompt
        elif disallow_prompt:
            sys.exit(f"Passphrase for {path} was not provided")
        # Request passphrase from user
        else:
            from getpass import getpass
            attempts = 3
            while attempts > 0:
                try:
                    secret = getpass(f"Config file is encrypted, please enter the passphrase for {path} (leave empty to abort): ").encode('utf-8')
                    if secret == b'':    # Abort
                        sys.exit(f"Aborted by user")
                except Exception as err:
                    print_exception_secret()
                    sys.exit(f"Unable to read passphrase")

                try:    # Decrypt
                    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
                    key = kdf.derive(secret)

                    cypher = enc_config['cypher'].encode('utf-8')
                    config_json = json.loads(jwe.decrypt(cypher, key))
                    break
                except jwe.JWEError as err: # Invalid, ask again
                    print(f"Unable to load {path}: Invalid config passphrase provided")
                    attempts -= 1
                except Exception as err:
                    print_exception_secret()
                    sys.exit(f"Unable to decrypt config")

            if attempts == 0:
                sys.exit(f"Did you forget your passphrase for {path} ? Go to http://localhost:8080/ to recreate the file")

    return Struct(config_json)

def generate_paths(traits: Struct = None):
    paths = Struct()
    paths.user_folder = os.path.join(".", "collections")
    if traits:
        paths.collection = os.path.join(paths.user_folder, traits.collection_lower)
        paths.ipfs_folder = os.path.join(paths.collection, "ipfs")
        paths.metadata = os.path.join(paths.ipfs_folder, "metadata")
        paths.images = os.path.join(paths.ipfs_folder, "images")
        paths.thumbnails = os.path.join(paths.ipfs_folder, "thumbnails")

        paths.gen_conf = os.path.join(paths.collection, "config")
        paths.source = os.path.join(paths.gen_conf, "source_layers")
        paths.metadata_cids = os.path.join(paths.gen_conf, "metadata-cids.json")

        paths.stats = os.path.join(paths.collection, "stats")
        paths.all_traits = os.path.join(paths.stats, "all-traits.json")
        paths.gen_stats = os.path.join(paths.stats, "gen-stats.json")

    # Log files
    paths.mint_info = os.path.join(paths.user_folder, "mint-info.json")
    paths.transfer_info = os.path.join(paths.user_folder, "transfer-info.json")

    # Config files
    paths.config = os.path.join(".", ".secrets", "config.json")
    paths.transfer_config = os.path.join(".", ".secrets", "transfer_config.json")

    paths.custom_output = os.path.join(paths.user_folder, "custom")
    paths.custom_metadata_cids = os.path.join(paths.custom_output, 'metadata-cids.json')
    paths.custom_metadata = os.path.join(paths.custom_output, 'metadata')

    return paths

def get_variation_cnt(layers: list):
    cnt = 1
    for layer in layers:
        cnt *= len(layer["weights"])
    return cnt

def set_progress_for_ui(op: str, completed: int, total: int):
    with open("php/progress.json", "w+") as progress_file:
        json.dump({
                "operation": op,
                "completed": completed,
                "total": total
            },
            progress_file
        )
    os.chmod("php/progress.json", 0o777)

# JSON conversion
class SemVerFilter(object):
    regex = r"^(?P<major>x|0|[1-9]\d*)\.(?P<minor>x|0|[1-9]\d*)\.(?P<patch>x|0|[1-9]\d*)?$"
    filter: str
    elements: list
    priority: int   # Lower number means higher priority
    match_regex: str

    def __init__(self, ver_filter: str):
        self.filter = ver_filter.replace("v", "").strip()
        # Extract major, minor, patch elements
        m = re.match(self.regex, self.filter)
        assert m is not None, f"Invalid version filter {ver_filter}"
        self.elements = [m.group('major'), m.group('minor'), m.group('patch')]

        # Validate wildcard position, calculate priority rank
        wildcard_found = False
        self.priority = 0
        for i,el in enumerate(self.elements):
            if wildcard_found and el != "x":
                raise Exception(f"Invalid version filter, numeral found after wildcard {ver_filter}")
            elif el == "x":
                if not wildcard_found:
                    self.priority = 3 - i
                wildcard_found = True

        self.match_regex = r"^" + r"\.".join(self.elements).replace('x', r"(0|[1-9]\d*)") + r"$"

        super().__init__()

    def get_priority(self) -> int:
        return self.priority

    def match(self, ver: 'SemVerFilter') -> bool:
        assert ver.get_priority() == 0, f"SemVerFilter cannot match to version with wildcard {ver}"
        return re.match(self.match_regex, ver.filter) is not None

    def __repr__(self) -> str:
        return f"{self.elements[0]}.{self.elements[1]}.{self.elements[2]}"

    def __hash__(self) -> int:
        return hash((self.elements[0], self.elements[1], self.elements[2]))

class FromToFilter(object):
    def __init__(self, f: SemVerFilter, t: SemVerFilter) -> None:
        self.f = f
        self.t = t
        super().__init__()

    def get_priority(self) -> int:
        return self.f.get_priority() + self.t.get_priority()

    def sort_func(self) -> int:
        return self.get_priority()

    def match(self, fromto: 'FromToFilter') -> bool:
        return self.f.match(fromto.f) and self.t.match(fromto.t)

    def __repr__(self) -> str:
        return f"{self.f} -> {self.t}"

    def __hash__(self):
        return hash((self.f, self.t))

Key = TypeVar('Key', bound=FromToFilter)
Route = TypeVar('Route')

class Router(Generic[Key, Route]):
    routes: 'OrderedDict[Key, Route]'

    def __init__(self) -> None:
        self.routes = OrderedDict()
        super().__init__()

    def add_map(self, key: Key, route: Route) -> None:
        self.routes[key] = route
        s = sorted(self.routes.items(), key=lambda kv_pair: kv_pair[0].sort_func())
        self.routes = OrderedDict(s)

    def match_route(self, filter: FromToFilter) -> Route:
        for key, route in self.routes.items():
            if key.match(filter):
                return route

        return None

# [END] JSON conversion