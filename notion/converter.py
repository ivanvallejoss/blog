def blocks_to_markdown(blocks: list) -> str:
    markdown_parts = []
    for block in blocks:
        match block["type"]:
            case "heading_2":
                markdown_parts.append(f"## {"".join(rt["plain_text"] for rt in block["heading_2"]["rich_text"])}\n\n")
            case "heading_3":
                markdown_parts.append(f"### {"".join(rt["plain_text"] for rt in block["heading_3"]["rich_text"])}\n\n")
            case "paragraph":
                markdown_parts.append(f"{"".join(rt["plain_text"] for rt in block["paragraph"]["rich_text"])}\n\n")
            case "code":
                markdown_parts.append(f"```{block["code"]["language"]}\n" f"{"".join(rt["plain_text"] for rt in block["code"]["rich_text"])}\n```\n\n")
            case _:
                pass

    return "".join(markdown_parts)