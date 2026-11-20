from notion_client import Client
from notion_client.helpers import collect_paginated_api
import os
from datetime import datetime
from dotenv import load_dotenv

from .converter import CHILD_TYPES

load_dotenv()

notion = Client(auth=os.environ.get("NOTION_TOKEN"))
DATA_SOURCE_ID = os.environ.get("NOTION_DATA_SOURCE_ID")


def get_posts(filtro="Published"):
    """
    Funcion que devuelve los posts existentes en Notion.
    Es posible filtrar de forma personalizada, no filtrar o filtrar por default.
    """
    params = {"data_source_id": DATA_SOURCE_ID}

    if filtro is not None:
        params["filter"] = {
            "property": "Estado",
            "status": {"equals": filtro}
        }

    # Notion devuelve como máximo 100 resultados por pedido: se sigue el cursor.
    return collect_paginated_api(notion.data_sources.query, **params)


def get_page_blocks(page_id):
    """
    Bloques de una página (o de un bloque) de Notion, con sus hijos.

    Notion devuelve como máximo 100 bloques por pedido: se sigue el cursor
    hasta el final. Los bloques con `has_children` de un tipo que el conversor
    sabe anidar (listas, citas…, ver `CHILD_TYPES`) traen sus hijos en la
    clave `children`, pedidos de la misma forma. Los de tipos no soportados no
    se recorren: no se van a convertir.

    Solo lectura: no escribe nada en Notion.
    """
    blocks = collect_paginated_api(notion.blocks.children.list, block_id=page_id)
    for block in blocks:
        if block.get("has_children") and block.get("type") in CHILD_TYPES:
            block["children"] = get_page_blocks(block["id"])
    return blocks


def get_details_from_post(notion_post):
    """
    Funcion helper para obtener la metadata de cada post de Notion.
    param [notion_post] -> metadata de un post dentro de la base de datos en Notion.
    return -> post_details: 
                    'title': Titulo, 
                    'slug': slug, 
                    'category_name': nombre de la categoria (puede ser None si en Notion no se marco una),
                    'published_at': fecha y hora de creacion,
                    'notion_id': id de la pagina,
                    'synced_at': last_edited_time.
    """
    notion_post = notion_post

    post_details = {
        'notion_id': notion_post["id"],
        'title': "".join(rt["plain_text"] for rt in notion_post["properties"]["Titulo"]["title"]),
        'slug':     "".join(rt["plain_text"] for rt in notion_post["properties"]["slug"]["rich_text"]),
        'published_at': datetime.fromisoformat(notion_post["properties"]["Fecha Publicacion"]["date"]["start"]).replace(tzinfo=None),
        'synced_at': datetime.fromisoformat(notion_post["last_edited_time"]).replace(tzinfo=None),
    }

    # Manejo separado de la propiedad `category_name`
    # Se tiene en cuenta el caso en donde esta provenga vacia desde Notion.
    category_property = notion_post["properties"]["categoria"]["select"]
    post_details["category_name"] = category_property["name"] if category_property else None

    return post_details
