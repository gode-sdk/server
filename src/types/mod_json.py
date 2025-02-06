# mod_json.py

import re
import json
import hashlib
import zipfile
from io import BytesIO, BufferedReader
from urllib.parse import urlparse

import semver
from PIL import Image

# --- Placeholder Classes for Domain Types ---
# In your Rust code these are defined elsewhere.
# Replace these with your actual implementations if available.
class DependencyImportance:
    @staticmethod
    def default():
        return "default"

class ModVersionCompare:
    MoreEq = "MoreEq"
    LessEq = "LessEq"
    Exact = "Exact"
    Less = "Less"
    More = "More"

class IncompatibilityImportance:
    @staticmethod
    def default():
        return "default"

class DependencyCreate:
    def __init__(self, dependency_id, version, compare, importance):
        self.dependency_id = dependency_id
        self.version = version
        self.compare = compare
        self.importance = importance

class IncompatibilityCreate:
    def __init__(self, incompatibility_id, version, compare, importance):
        self.incompatibility_id = incompatibility_id
        self.version = version
        self.compare = compare
        self.importance = importance

class DetailedGDVersion:
    def __init__(self, data):
        self.data = data

class ApiError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

# --- ModJson and Related Types ---

class ModJson:
    def __init__(self, data: dict):
        self.geode = data.get("geode", "")
        self.version = data.get("version", "")
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.developer = data.get("developer")
        self.developers = data.get("developers")
        self.description = data.get("description")
        self.repository = data.get("repository")
        self.tags = data.get("tags")
        self.windows = data.get("windows", False)
        self.ios = data.get("ios", False)
        self.android32 = data.get("android32", False)
        self.android64 = data.get("android64", False)
        self.mac_intel = data.get("mac_intel", False)
        self.mac_arm = data.get("mac_arm", False)
        self.download_url = data.get("download_url", "")
        self.hash = data.get("hash", "")
        self.early_load = data.get("early-load", False)
        self.api = data.get("api")
        self.gd = DetailedGDVersion(data.get("gd", {}))
        self.logo = data.get("logo", b"")
        self.about = data.get("about")
        self.changelog = data.get("changelog")
        self.dependencies = data.get("dependencies")
        self.incompatibilities = data.get("incompatibilities")
        self.links = data.get("links")

    @staticmethod
    def from_zip(zip_bytes: bytes, download_url: str, store_image: bool, max_size_mb: int) -> "ModJson":
        max_size_bytes = max_size_mb * 1_000_000
        if len(zip_bytes) > max_size_bytes:
            raise ApiError("File size exceeds maximum allowed size")
        # Calculate SHA256 hash
        file_hash = hashlib.sha256(zip_bytes).hexdigest()
        with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
            if "mod.json" not in archive.namelist():
                raise ApiError("mod.json not found")
            with archive.open("mod.json") as json_file:
                data = json.load(json_file)
        data["version"] = data.get("version", "").lstrip("v")
        data["hash"] = file_hash
        data["download_url"] = parse_download_url(download_url)
        mod_json = ModJson(data)
        # Process other files in the archive
        with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
            for name in archive.namelist():
                with archive.open(name) as file:
                    if name.endswith(".dll"):
                        mod_json.windows = True
                    elif name.endswith(".ios.dylib"):
                        mod_json.ios = True
                    elif name.endswith(".dylib"):
                        arm, intel = check_mac_binary(file)
                        mod_json.mac_arm = arm
                        mod_json.mac_intel = intel
                    elif name.endswith(".android32.so"):
                        mod_json.android32 = True
                    elif name.endswith(".android64.so"):
                        mod_json.android64 = True
                    elif name == "about.md":
                        mod_json.about = file.read().decode("utf-8")
                    elif name == "changelog.md":
                        mod_json.changelog = file.read().decode("utf-8")
                    elif name == "logo.png":
                        mod_json.logo = validate_mod_logo(file, store_image)
        return mod_json

    def prepare_dependencies_for_create(self):
        deps = self.dependencies
        result = []
        if deps is None:
            return result

        if isinstance(deps, list):  # Old format
            for dep in deps:
                if dep.get("version") == "*":
                    result.append(DependencyCreate(
                        dependency_id=dep.get("id"),
                        version="*",
                        compare=ModVersionCompare.MoreEq,
                        importance=dep.get("importance", DependencyImportance.default())
                    ))
                else:
                    dependency_ver, compare = split_version_and_compare(dep.get("version"))
                    result.append(DependencyCreate(
                        dependency_id=dep.get("id"),
                        version=str(dependency_ver),
                        compare=compare,
                        importance=dep.get("importance", DependencyImportance.default())
                    ))
        elif isinstance(deps, dict):  # New format
            for dep_id, dep in deps.items():
                if isinstance(dep, str):
                    dependency_ver, compare = split_version_and_compare(dep)
                    result.append(DependencyCreate(
                        dependency_id=dep_id,
                        version=str(dependency_ver),
                        compare=compare,
                        importance=DependencyImportance.default()
                    ))
                elif isinstance(dep, dict):
                    dependency_ver, compare = split_version_and_compare(dep.get("version"))
                    result.append(DependencyCreate(
                        dependency_id=dep_id,
                        version=str(dependency_ver),
                        compare=compare,
                        importance=dep.get("importance", DependencyImportance.default())
                    ))
        return result

    def prepare_incompatibilities_for_create(self):
        incompat = self.incompatibilities
        result = []
        if incompat is None:
            return result

        if isinstance(incompat, list):  # Old format
            for inc in incompat:
                if inc.get("version") == "*":
                    result.append(IncompatibilityCreate(
                        incompatibility_id=inc.get("id"),
                        version="*",
                        compare=ModVersionCompare.MoreEq,
                        importance=inc.get("importance", IncompatibilityImportance.default())
                    ))
                else:
                    ver, compare = split_version_and_compare(inc.get("version"))
                    result.append(IncompatibilityCreate(
                        incompatibility_id=inc.get("id"),
                        version=str(ver),
                        compare=compare,
                        importance=inc.get("importance", IncompatibilityImportance.default())
                    ))
        elif isinstance(incompat, dict):  # New format
            for inc_id, item in incompat.items():
                if isinstance(item, str):
                    ver, compare = split_version_and_compare(item)
                    result.append(IncompatibilityCreate(
                        incompatibility_id=inc_id,
                        version=str(ver),
                        compare=compare,
                        importance=IncompatibilityImportance.default()
                    ))
                elif isinstance(item, dict):
                    ver, compare = split_version_and_compare(item.get("version"))
                    result.append(IncompatibilityCreate(
                        incompatibility_id=inc_id,
                        version=str(ver),
                        compare=compare,
                        importance=item.get("importance", IncompatibilityImportance.default())
                    ))
        return result

    def validate(self):
        id_regex = re.compile(r"^[a-z0-9_\-]+\.[a-z0-9_\-]+$")
        if not id_regex.match(self.id):
            raise ApiError(f"Invalid mod id {self.id} (lowercase and numbers only, needs to look like 'dev.mod')")
        if not self.developer and not self.developers:
            raise ApiError("No developer specified on mod.json")
        if len(self.id) > 64:
            raise ApiError("Mod id too long (max 64 characters)")
        if self.links:
            for key in ["community", "homepage", "source"]:
                url = self.links.get(key)
                if url:
                    try:
                        urlparse(url)
                    except Exception as e:
                        raise ApiError(f"Invalid {key} URL: {url}. Reason: {e}")

def validate_mod_logo(file, return_bytes: bool) -> bytes:
    try:
        data = file.read()
        image = Image.open(BytesIO(data))
        width, height = image.size
        if width != height:
            raise ApiError(f"Mod logo must have 1:1 aspect ratio. Current size is {width}x{height}")
        if width > 336 or height > 336:
            image = image.resize((336, 336), Image.LANCZOS)
        if return_bytes:
            with BytesIO() as output:
                image.save(output, format="PNG")
                return output.getvalue()
        return b""
    except Exception as e:
        raise ApiError(f"Invalid logo.png: {str(e)}")

def split_version_and_compare(ver: str):
    copy = ver
    compare = ModVersionCompare.MoreEq
    if ver.startswith("<="):
        copy = ver[2:]
        compare = ModVersionCompare.LessEq
    elif ver.startswith(">="):
        copy = ver[2:]
        compare = ModVersionCompare.MoreEq
    elif ver.startswith("="):
        copy = ver[1:]
        compare = ModVersionCompare.Exact
    elif ver.startswith("<"):
        copy = ver[1:]
        compare = ModVersionCompare.Less
    elif ver.startswith(">"):
        copy = ver[1:]
        compare = ModVersionCompare.More
    copy = copy.lstrip("v")
    try:
        v = semver.VersionInfo.parse(copy)
        return (v, compare)
    except ValueError:
        raise ApiError(f"Invalid semver {ver}")

def parse_download_url(url: str) -> str:
    return url.rstrip("\\/")

def check_mac_binary(file) -> (bool, bool):
    try:
        file.seek(0)
        b = file.read(12)
        if len(b) < 12:
            raise ApiError("Invalid MacOS binary")
        is_fat_arch = b[0] == 0xCA and b[1] == 0xFE and b[2] == 0xBA and b[3] == 0xBE
        is_single_platform = b[0] == 0xCF and b[1] == 0xFA and b[2] == 0xED and b[3] == 0xFE
        if is_fat_arch:
            num_arches = b[7]
            if num_arches == 0x1:
                first = b[8]
                second = b[11]
                if first == 0x1 and second == 0x7:
                    return (False, True)
                elif first == 0x1 and second == 0xC:
                    return (True, False)
                else:
                    raise ApiError("Invalid MacOS binary")
            elif num_arches == 0x2:
                return (True, True)
            else:
                raise ApiError("Invalid MacOS binary")
        elif is_single_platform:
            first = b[4]
            second = b[7]
            if first == 0x7 and second == 0x1:
                return (False, True)
            elif first == 0xC and second == 0x1:
                return (True, False)
        raise ApiError("Invalid MacOS binary")
    except Exception as e:
        raise ApiError(str(e))
