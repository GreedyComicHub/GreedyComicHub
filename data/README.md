# Data Directory

Berisi file JSON untuk GreedyComicHub:
- `<comic>.json` (e.g., `magic-emperor.json`): Metadata komik (judul, author, synopsis, cover) dan chapters (key: `chapters[chapter].pages` untuk URL gambar).
- `index.json`: Daftar komik (judul, author, synopsis, cover, total_chapters).

Struktur JSON:
```json
// magic-emperor.json
{
  "title": "Magic Emperor",
  "author": "Unknown Author",
  "synopsis": "...",
  "cover": "https://res.cloudinary.com/...",
  "chapters": {
    "1": {
      "pages": ["https://res.cloudinary.com/.../page_1.jpg", ...]
    }
  }
}