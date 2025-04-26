# pythonvCard4

A **RFC 6350‑compliant vCard 4.0** parser and generator for Python.

## Features

- Create vCard (.vcf) files from Python `Contact` objects
- Parse existing vCard files back into `Contact` instances
- Support for names, emails, multiple phone numbers, addresses, URLs, social profiles, photos, dates, and more
- Inline image embedding (resize + Base64 encode)
- Extension properties (`X-` fields) via `custom` and `social_profiles`
- Full round‑trip fidelity, folding/unfolding, and escaping per spec

## Installation

Install via [PyPI](https://pypi.org/project/pythonvCard4/):

```bash
pip install pythonvCard4
```

## Quick Start

### 1. Create a vCard

```python
from datetime import date
from pythonvCard4.vcard import Contact

# Build a Contact
c = Contact(
    fn="Jane Doe",
    n=["Doe","Jane","","",""] ,
    email=[{"value": "jane@example.com", "type": ["work"]}],
    tel=[
        {"value": "+1234567890", "type": ["cell"]},
        {"value": "+0987654321", "type": ["home"]}
    ],
    url=["https://janedoe.dev"],
    bday=date(1990, 5, 15),
)

# Add a Twitter profile
c.social_profiles.append({
    "type": ["twitter"],
    "value": "http://twitter.com/janedoe"
})

# Embed a photo (JPEG)
c.photo_path = "path/to/photo.jpg"

# Serialize to vCard text
vcf_text = c.to_vcard()
print(vcf_text)
```

### 2. Parse an existing vCard
```python
from pythonvCard4.vcard import Contact

# Load from file
vcf_text = open('jane.vcf', 'r', encoding='utf-8').read()
contact = Contact.from_vcard(vcf_text)

print(contact.fn)
print(contact.tel)
print(contact.social_profiles)
```

## Documentation & Support

See [GitHub](https://github.com/sharf-shawon/pythonvCard4 for full docs, examples, and issue tracking.
