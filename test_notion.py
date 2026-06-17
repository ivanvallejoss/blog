from notion.client import get_posts, get_page_blocks
from notion.converter import blocks_to_markdown
import json

posts = get_posts()
first_post = posts[1]

page_id = first_post["id"]
blocks = get_page_blocks(page_id)
markdown = blocks_to_markdown(blocks)

print(json.dumps(first_post, indent=2))