from __future__ import unicode_literals


def get_data():
    """Customise Module page."""
    return [
        {
            "label": "Set up",
            "items": [
                {
                    "type": "doctype",
                    "name": "Attachment Settings",
                    "description": "Attachment Settings records",
                },
                {
                    "type": "doctype",
                    "name": "Frappe S3 Attachment",
                    "label": "S3 Attachment Settings",
                }
            ]
        }
    ]
