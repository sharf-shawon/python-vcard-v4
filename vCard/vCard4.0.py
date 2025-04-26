import re
import base64
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import List, Dict, Optional, Union
from PIL import Image
import io

__version__ = "0.2.0"

# Exceptions
class VCardError(Exception):
    """Base exception for vCard errors."""
    pass

class ValidationError(VCardError):
    """Raised when a vCard fails validation."""
    pass

# Utility functions

def escape_text(text: str) -> str:
    """Escape special characters in property values."""
    return (text.replace('\\', '\\\\')
                .replace(';', '\\;')
                .replace(',', '\\,')
                .replace('\n', '\\n'))


def unescape_text(text: str) -> str:
    """Unescape text from vCard value encoding."""
    return (text.replace('\\n', '\n')
                .replace('\\,', ',')
                .replace('\\;', ';')
                .replace('\\\\', '\\'))


def fold_line(line: str, limit: int = 75) -> List[str]:
    """Fold a single line according to RFC 6350 at limit chars."""
    parts = []
    while len(line) > limit:
        parts.append(line[:limit])
        line = ' ' + line[limit:]
    parts.append(line)
    return parts if parts else [line]


def unfold_lines(lines: List[str]) -> List[str]:
    """Unfold folded vCard lines into logical lines."""
    unfolded: List[str] = []
    for line in lines:
        if line.startswith((' ', '\t')) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded

@dataclass
class Contact:
    # Required
    fn: str  # Formatted Name
    # Name components: family, given, additional, prefixes, suffixes
    n: Optional[List[str]] = None
    # Optional standard properties
    nickname: List[str] = field(default_factory=list)
    photo_path: Optional[str] = None
    photo_data: Optional[str] = None  # base64-encoded
    bday: Optional[date] = None
    anniversary: Optional[date] = None
    gender: Optional[str] = None
    email: List[Dict[str, Union[str, List[str]]]] = field(default_factory=list)
    tel: List[Dict[str, Union[str, List[str]]]] = field(default_factory=list)
    adr: List[Dict[str, Union[List[str], List[str]]]] = field(default_factory=list)
    org: Optional[List[str]] = None
    title: Optional[str] = None
    role: Optional[str] = None
    url: List[str] = field(default_factory=list)
    impp: List[str] = field(default_factory=list)
    uid: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    note: Optional[str] = None
    prodid: Optional[str] = None
    rev: Optional[str] = None
    tz: Optional[str] = None
    geo: Optional[Dict[str, float]] = None
    # Custom properties
    custom: Dict[str, Union[str, List[str]]] = field(default_factory=dict)
    social_profiles: List[Dict[str, Union[str, List[str]]]] = field(default_factory=list)

    def to_vcard(self) -> str:
        """Convert Contact instance into a vCard 4.0 string."""
        lines: List[str] = ['BEGIN:VCARD', 'VERSION:4.0']
        # FN
        lines += fold_line(f'FN:{escape_text(self.fn)}')
        # N
        if self.n:
            comps = [escape_text(c) if c else '' for c in self.n]
            lines += fold_line(f'N:{";".join(comps)}')
        # Nickname
        if self.nickname:
            lines += fold_line(f'NICKNAME:{";".join(escape_text(n) for n in self.nickname)}')
        # Photo
        if self.photo_path:
            self._embed_photo()
        if self.photo_data:
            lines += fold_line(f'PHOTO;ENCODING=b;MEDIATYPE=image/jpeg:{self.photo_data}')
        # Birthday & Anniversary
        if self.bday:
            lines += fold_line(f'BDAY:{self.bday.isoformat()}')
        if self.anniversary:
            lines += fold_line(f'ANNIVERSARY:{self.anniversary.isoformat()}')
        # Gender
        if self.gender:
            lines += fold_line(f'GENDER:{escape_text(self.gender)}')
        # Emails
        for e in self.email:
            params = ''
            if 'type' in e:
                params = f';TYPE={",".join(e["type"])}'
            lines += fold_line(f'EMAIL{params}:{escape_text(e["value"])}')
        # Phones
        for t in self.tel:
            params = ''
            if 'type' in t:
                params = f';TYPE={",".join(t["type"])}'
            lines += fold_line(f'TEL{params}:{escape_text(t["value"])}')
        # Addresses
        for a in self.adr:
            params = ''
            if 'type' in a:
                params = f';TYPE={",".join(a["type"])}'
            comps = [escape_text(x) for x in a.get('value', ['']*7)]
            lines += fold_line(f'ADR{params}:{";".join(comps)}')
        # Organization
        if self.org:
            lines += fold_line(f'ORG:{";".join(escape_text(o) for o in self.org)}')
        # Title & Role
        if self.title:
            lines += fold_line(f'TITLE:{escape_text(self.title)}')
        if self.role:
            lines += fold_line(f'ROLE:{escape_text(self.role)}')
        # URLs
        for u in self.url:
            lines += fold_line(f'URL:{escape_text(u)}')
        # IMPP
        for im in self.impp:
            lines += fold_line(f'IMPP:{escape_text(im)}')
        # UID, PRODID, REV, TZ, GEO, CATEGORIES, NOTE
        if self.uid:
            lines += fold_line(f'UID:{escape_text(self.uid)}')
        if self.prodid:
            lines += fold_line(f'PRODID:{escape_text(self.prodid)}')
        if self.rev:
            lines += fold_line(f'REV:{escape_text(self.rev)}')
        if self.tz:
            lines += fold_line(f'TZ:{escape_text(self.tz)}')
        if self.geo:
            lines += fold_line(f'GEO:{self.geo["lat"]};{self.geo["lon"]}')
        if self.categories:
            lines += fold_line(f'CATEGORIES:{",".join(escape_text(c) for c in self.categories)}')
        if self.note:
            lines += fold_line(f'NOTE:{escape_text(self.note)}')
        
        # Custom
        for k, v in self.custom.items():
            if isinstance(v, list):
                val = ";".join(escape_text(x) for x in v)
            else:
                val = escape_text(str(v))
            lines += fold_line(f'{k.upper()}:{val}')

        # serialize social profiles:
        for sp in self.social_profiles:
            types = ";TYPE=" + ",".join(sp.get("type", [])) if sp.get("type") else ""
            lines += fold_line(f"X-SOCIALPROFILE{types}:{escape_text(sp['value'])}")

        lines.append('END:VCARD')
        return '\r\n'.join(lines) + '\r\n'

    def _embed_photo(self, max_size: int = 300) -> None:
        """Resize and encode photo for vCard."""
        with Image.open(self.photo_path) as img:
            img.thumbnail((max_size, max_size))
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            self.photo_data = base64.b64encode(buf.getvalue()).decode('ascii')

    @staticmethod
    def from_vcard(vcard_text: str) -> 'Contact':
        """Parse vCard string into a Contact instance."""
        lines = unfold_lines(vcard_text.splitlines())
        props: Dict[str, List[str]] = {}
        params_map: Dict[str, List[Dict[str, Union[str,List[str]]]]] = {}
        for line in lines:
            if ':' not in line:
                continue
            key_part, value = line.split(':', 1)
            parts = key_part.split(';')
            name = parts[0].upper()
            params = {}
            for p in parts[1:]:
                if '=' in p:
                    k, v = p.split('=', 1)
                    params[k.lower()] = v.split(',')
            params_map.setdefault(name, []).append({'params': params, 'value': unescape_text(value)})
        # Required FN
        if 'FN' not in params_map:
            raise ValidationError('FN is required')
        contact = Contact(fn=params_map['FN'][0]['value'])
        # N
        if 'N' in params_map:
            contact.n = params_map['N'][0]['value'].split(';')
        # Populate fields
        for name, entries in params_map.items():
            for entry in entries:
                if name == 'EMAIL':
                    contact.email.append({'value': entry['value'], 'type': entry['params'].get('type', [])})
                elif name == 'TEL':
                    contact.tel.append({'value': entry['value'], 'type': entry['params'].get('type', [])})
                elif name == 'ADR':
                    contact.adr.append({'value': entry['value'].split(';'), 'type': entry['params'].get('type', [])})
                elif name == 'PHOTO' and 'ENCODING' in entry['params']:
                    contact.photo_data = entry['value']
                elif name == 'BDAY':
                    contact.bday = date.fromisoformat(entry['value'])
                elif name == 'ANNIVERSARY':
                    contact.anniversary = date.fromisoformat(entry['value'])
                elif name == 'URL':
                    contact.url.append(entry['value'])
                elif name == 'IMPP':
                    contact.impp.append(entry['value'])
                elif name == 'NICKNAME':
                    contact.nickname = entry['value'].split(';')
                elif name == 'UID':
                    contact.uid = entry['value']
                elif name == 'PRODID':
                    contact.prodid = entry['value']
                elif name == 'REV':
                    contact.rev = entry['value']
                elif name == 'TZ':
                    contact.tz = entry['value']
                elif name == 'GEO':
                    lat, lon = entry['value'].split(';')
                    contact.geo = {'lat': float(lat), 'lon': float(lon)}
                elif name == 'GENDER':
                    contact.gender = entry['value']
                elif name == 'CATEGORIES':
                    contact.categories = entry['value'].split(',')
                elif name == 'NOTE':
                    contact.note = entry['value']
                elif name not in ('BEGIN', 'END', 'VERSION'):
                    # treat as custom
                    contact.custom.setdefault(name, []).append(entry['value'])
        return contact

# Example usage
if __name__ == '__main__':
    # Create a contact
    c = Contact(
        fn='Jane Doe',
        n=['Doe','Jane','','',''],
        email=[{'value':'jane.doe@example.com','type':['work']}],
        tel=[
          {'value':'+123456789','type':['cell']},
          {'value':'+234567890','type':['cell']},
          {'value':'+345678900','type':['cell']},
          {'value':'+456789000','type':['cell']},
        ],
        url=['https://janedoe.dev'],
        # photo_path='jane.jpg'
    )
    c.social_profiles.append({
      "type": ["twitter"],
      "value": "http://twitter.com/sharf.shawon"
    })
    vcf = c.to_vcard()
    print(vcf)
    # Parse back
    parsed = Contact.from_vcard(vcf)
    print(parsed)
