import io

from typing import *
from datetime import datetime

def list_id_doc(list_id: str):
    """
    Memprosess list_id yang berupa text.
    Untuk dijadikan bytes dan list id bertipe data List.

    :params list_id (str): Daftar id document
    """
    doc = io.BytesIO(list_id.encode())
    doc.name = f"daftar-id-{datetime.now().strftime('%Y%m%dT%H%M%S')}.txt"
    
    listId: List[str] = list_id.split("\n")
    return doc, listId