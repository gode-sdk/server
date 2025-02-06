import zipfile
import json
import hashlib
import re
from typing import List, Optional, Dict, Union
from urllib.parse import urlparse
import semver
from io import BytesIO
from PIL import Image
from requests import get
from requests.exceptions import RequestException


class ApiError(Exception):
    pass


class DependencyImportance:
    """Placeholder class for DependencyImportance"""
    pass


class IncompatibilityImportance:
    """Placeholder class for IncompatibilityImportance"""
    pass


class ModJson:
    def __init__(self, data: dict):
        self.geode: str = data.get('geode', '')
        self.version: str = data.get('version', '')
        self.id: str = data.get('id', '')
        self.name: str = data.get('name', '')
        self.developer: Optional[str] = data.get('developer')
        self.developers: Optional[List[str]] = data.get('developers')
        self.description: Optional[str] = data.get('description')
        self.repository: Optional[str] = data.get('repository')
        self.tags: Optional[List[str]] = data.get('tags')
        self.windows: bool = data.get('windows', False)
        self.ios: bool = data.get('ios', False)
        self.android32: bool = data.get('android32', False)
        self.android64: bool = data.get('android64', False)
        self.mac_intel: bool = data.get('mac_intel', False)
        self.mac_arm: bool = data.get('mac_arm', False)
        self.download_url: str = data.get('download_url', '')
        self.hash: str = data.get('hash', '')
        self.early_load: bool = data.get('early-load', False)
        self.api: Optional[dict] = data.get('api')
        self.gd: 'DetailedGDVersion' = data.get('gd')
        self.logo: List[bytes] = data.get('logo', [])
        self.about: Optional[str] = data.get('about')
        self.changelog: Optional[str] = data.get('changelog')
        self.dependencies: Optional[Union[List[dict], Dict[str, dict]]] = data.get('dependencies')
        self.incompatibilities: Optional[Union[List[dict], Dict[str, dict]]] = data.get('incompatibilities')
        self.links: Optional[dict] = data.get('links')


    def validate(self) -> None:
        id_regex = re.compile(r"^[a-z0-9_\-]+\.[a-z0-9_\-]+$")
        if not id_regex.match(self.id):
            raise ApiError(f"Invalid mod id {self.id} (lowercase and numbers only, needs to look like 'dev.mod')")
        
        if not self.developer and not self.developers:
            raise ApiError("No developer specified on mod.json")
        
        if len(self.id) > 64:
            raise ApiError("Mod id too long (max 64 characters)")
        
        if self.links:
            for link_type in ['community', 'homepage', 'source']:
                url = self.links.get(link_type)
                if url:
                    try:
                        urlparse(url)
                    except ValueError:
                        raise ApiError(f"Invalid {link_type} URL: {url}")
    

    @staticmethod
    def from_zip(file_path: str, download_url: str, store_image: bool, max_size_mb: int) -> 'ModJson':
        max_size_bytes = max_size_mb * 1_000_000
        with open(file_path, 'rb') as f:
            bytes_data = f.read(max_size_bytes)
            file_hash = hashlib.sha256(bytes_data).hexdigest()
            with zipfile.ZipFile(f) as zipf:
                if 'mod.json' not in zipf.namelist():
                    raise ApiError("mod.json not found")
                with zipf.open('mod.json') as json_file:
                    mod_json_data = json.load(json_file)
                    mod_json_data['hash'] = file_hash
                    mod_json_data['download_url'] = download_url
                    return ModJson(mod_json_data)


    def prepare_dependencies_for_create(self) -> List[dict]:
        # Handle dependency preparation logic here (simplified from original)
        dependencies = []
        if not self.dependencies:
            return dependencies
        
        if isinstance(self.dependencies, list):  # old format
            for dep in self.dependencies:
                dependencies.append({
                    'dependency_id': dep.get('id'),
                    'version': dep.get('version'),
                    'importance': dep.get('importance', DependencyImportance())
                })
        elif isinstance(self.dependencies, dict):  # new format
            for dep_id, dep in self.dependencies.items():
                dependencies.append({
                    'dependency_id': dep_id,
                    'version': dep.get('version'),
                    'importance': dep.get('importance', DependencyImportance())
                })
        return dependencies
    

    @staticmethod
    def parse_download_url(url: str) -> str:
        return url.rstrip("/")


def validate_mod_logo(file_path: str, return_bytes: bool = True) -> bytes:
    try:
        with open(file_path, 'rb') as file:
            image = Image.open(file)
            if image.width != image.height:
                raise ApiError(f"Mod logo must have 1:1 aspect ratio. Current size is {image.width}x{image.height}")
            if image.width > 336 or image.height > 336:
                image = image.resize((336, 336))
            if return_bytes:
                with BytesIO() as byte_io:
                    image.save(byte_io, format='PNG')
                    return byte_io.getvalue()
            return b""
    except Exception as e:
        raise ApiError(f"Invalid logo.png: {str(e)}")


def split_version_and_compare(ver: str) -> Union[tuple, None]:
    try:
        version = ver.lstrip('v')
        comparison_operator = ''
        if version.startswith("<="):
            version = version[2:]
            comparison_operator = '<='
        elif version.startswith(">="):
            version = version[2:]
            comparison_operator = '>='
        elif version.startswith('<'):
            version = version[1:]
            comparison_operator = '<'
        elif version.startswith('>'):
            version = version[1:]
            comparison_operator = '>'
        elif version.startswith('='):
            version = version[1:]
            comparison_operator = '='
        
        return (semver.Version(version), comparison_operator)
    except ValueError:
        raise ApiError(f"Invalid version string: {ver}")