import typer
from app.database import SessionLocal
from sync.services import sync_posts

app = typer.Typer()

@app.command()
def sync():
    """Sincroniza los posts desde Notion."""
    with SessionLocal() as db:
        sync_posts(db)


if __name__ == "__main__":
    app()