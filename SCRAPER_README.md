# GreedyComicHub - Manga Scraper CLI

Sistem otomatis untuk scrape manga dari komiku.org dengan ekstraksi chapter images, paraphrasing synopsis otomatis, dan integrasi dengan web interface.

## Fitur Utama

✅ **Scrape Manga** - Ambil semua metadata manga dari komiku.org
✅ **Chapter Images** - Extract URL gambar dari setiap chapter (tidak di-download)
✅ **Paraphrasing** - Synopsis otomatis diubah ke bahasa gaul Indonesia  
✅ **Update Smart** - Update hanya chapter yang belum ada (lebih cepat)
✅ **JSON Storage** - Format JSON terstandarisasi untuk web display
✅ **Anti-Detection** - User-agent rotation & random delays built-in

---

## 🎯 Command Reference

### 1. Scrape Semua Manga (Tipe Tertentu)

```bash
python -m python scrape manga
python -m python scrape manhua
python -m python scrape manhwa
```

**Apa yang terjadi:**
- Scrape list semua manga dari tipe yang dipilih (pagination)
- Skip manga yang sudah ada di database
- Untuk setiap manga baru: scrape metadata + semua chapter images
- Simpan ke `data/{slug}.json` dan update `data/index.json`
- Paraphrase synopsis ke bahasa gaul

**Waktu:** ~30 detik per manga (tergantung banyak chapter)

### 2. Scrape Satu Manga dari URL

```bash
python -m python scrape https://komiku.org/manga/50kg-cinderella/
```

**Contoh:**
```bash
python -m python scrape https://komiku.org/manga/solo-leveling-id/
python -m python scrape https://komiku.org/manga/dandadan/
```

**Apa yang terjadi:** Sama seperti di atas, hanya satu manga saja

### 3. Update Chapters (New Only) - REKOMENDASI UNTUK MAINTENANCE

```bash
# Update semua manga registered - hanya ambil chapter baru
python -m python update
```

**Atau lebih eksplisit:**
```bash
python -m python update-chapters
```

**Apa yang terjadi:**
- Baca list manga dari `data/index.json`
- Untuk setiap manga: cari chapter terakhir yang ada di database
- Ambil chapter baru saja dari web komiku
- Update `data/{slug}.json` dengan chapter baru
- LEBIH CEPAT karena tidak recheck existing chapters

**Waktu:** ~5-30 detik per manga (hanya check chapter baru)

**Kasus Penggunaan:**
```bash
# Setiap hari/minggu, update semua manga dengan chapter yang mungkin ada baru
python -m python update
```

### 4. Update Satu Manga (All Chapters) - Jika perlu recheck total

```bash
python -m python update-chapters https://komiku.org/manga/50kg-cinderella/
```

**Apa yang terjadi:**
- Scrape semua chapters dari URL tersebut (recheck dari awal)
- Replace existing chapters di `data/{slug}.json`
- LEBIH LAMBAT karena check semua, tapi memastikan lengkap

**Waktu:** ~1-5 menit per manga (tergantung banyak chapter)

**Kasus Penggunaan:**
```bash
# Jika ragu ada chapter yang terlewat atau chapter incomplete
python -m python update-chapters https://komiku.org/manga/solo-leveling-id/
```

### 5. Show Help & Command List

```bash
python -m python -help
python -m python --help
```

Menampilkan semua available commands dengan contoh penggunaan.

---

## 💾 Data Format

### Master Index: `data/index.json`

File yang dipake web untuk list & search manga.

```json
{
  "50kg-cinderella": {
    "title": "50kg Cinderella",
    "author": "Kim Yoon-Hee",
    "cover": "https://thumbnail.komiku.org/uploads/...",
    "sinopsis": "Cerita yang diparaphrase ke bahasa gaul, nggak mirip banget sama asli",
    "genre": "Romance, Comedy",
    "type": "Manga",
    "source_url": "https://komiku.org/manga/50kg-cinderella/",
    "total_chapters": 45
  },
  "solo-leveling-id": { ... },
  ...
}
```

### Individual Manga: `data/{slug}.json`

File yang dipake web untuk display detail & chapters saat user buka manga.

```json
{
  "title": "50kg Cinderella",
  "author": "Kim Yoon-Hee",
  "genre": "Romance, Comedy",
  "synopsis": "Cerita yang udah di-paraphrase ke bahasa gaul biar beda dari yang asli",
  "cover": "https://thumbnail.komiku.org/uploads/...",
  "source_url": "https://komiku.org/manga/50kg-cinderella/",
  "chapters": {
    "1": {
      "title": "Chapter 1",
      "url": "https://komiku.org/50kg-cinderella-chapter-01/",
      "images": [
        "https://img.komiku.org/uploads2/2503395-1.jpg",
        "https://img.komiku.org/uploads2/2503395-2_part1.jpg",
        "https://img.komiku.org/uploads2/2503395-2_part2.jpg"
      ]
    },
    "2": {
      "title": "Chapter 2",
      ...
    }
  }
}
```

---

## 📋 Typical Workflow

### Scenario 1: Initial Setup (Pertama kali)

```bash
# Scrape semua manga type - WAKTU LAMA (jam-jaman)
python -m python scrape manga
```

### Scenario 2: Maintenance (Rutin, misal seminggu sekali)

```bash
# Update semua manga dengan chapter yang ada baru - CEPAT
python -m python update
```

### Scenario 3: User request manga baru

```bash
# User: "Adain manga X"
python -m python scrape https://komiku.org/manga/X/

# Done! Manga muncul di web
```

### Scenario 4: Manga chapter incomplete

```bash
# Ternyata chapter suatu manga belum lengkap/ada yang terlewat
# Recheck dari awal:
python -m python update-chapters https://komiku.org/manga/X/
```

---

## 🔧 Konfigurasi & Technical Details

### Dependencies

`requirements.txt`:
```
selenium>=4.0.0
webdriver-manager>=3.8.0
beautifulsoup4>=4.11.0
requests>=2.28.0
```

Install:
```bash
pip install -r requirements.txt
```

### Anti-Detection Features (Built-in)

Scraper otomatis:
- ✅ Rotate random User-Agent setiap request
- ✅ Random delays 2-5 detik antara requests
- ✅ Proper HTTP headers (Accept, Referer, Connection)
- ✅ Session persistence (cookies)
- ✅ Error handling & retry logic
- ✅ Timeout handling (15 detik default)

### Performance

- **Requests library** - HTTP GET, super cepat
- **BeautifulSoup** - HTML parsing, efficient
- **No downloads** - Hanya ambil image URLs, tidak save file
- **Smart update** - Hanya scrape chapter baru kalau pakai `update`

Contoh waktu:
- Scrape 1 manga dengan 50 chapter: ~1-2 menit
- Update 100 manga (check chapter baru): ~5-10 menit
- Scrape 1000 manga baru: ~20-40 jam (depends on komiku stability)

---

## 📁 File Structure

```
python/
  __init__.py          # Package init
  __main__.py          # CLI entry point, main business logic
  scraper.py           # KomikuScraper - HTML parsing & extraction
  data_manager.py      # DataManager - JSON file I/O
  
data/
  index.json           # Master list semua manga
  {slug}.json          # Detail 1 manga + all chapters
  
SCRAPER_README.md      # Dokumentasi ini
requirements.txt       # Python dependencies
```

---

## 🎨 Web Integration

Cara web display fetch data:

1. **List manga** (`index.html`):
   - Baca `data/index.json`
   - Tampilkan di grid/list dengan cover + title

2. **Detail manga** (`comic.html?comic=dandadan`):
   - Baca `data/dandadan.json`
   - Tampilkan: cover, title, author, genre, synopsis, total chapters
   - Tampilkan list chapter dengan link

3. **Chapter reader** (`chapter-reader`):
   - Fetch image URLs dari chapter JSON
   - Display dalam image gallery
   - Swipe untuk next image

---

## 🐛 Troubleshooting

### Problem: Synopsis salah/blank

**Cause:** Komiku.org HTML structure kompleks, synopsis extraction kadang ambil text yang salah (misal login form).

**Solution:**
```bash
# Manual edit data/{slug}.json
# Update field "synopsis" dengan teks yang benar
```

**Future:** Bisa upgrade ke AI paraphraser API untuk lebih akurat

### Problem: Chapter images kosong/tidak terbaca

**Cause:** 
- Struktur HTML chapter page berbeda
- Komiku.org block request (rare, solved dengan user-agent rotation)
- Chapter belum publish fully

**Solution:**
1. Cek chapter URL di browser - apakah ada gambar?
2. Jika ada, coba scrape ulang dengan:
   ```bash
   python -m python update-chapters https://komiku.org/manga/X/
   ```

### Problem: Timeout / Connection error

**Cause:** Komiku.org unstable/slow

**Solution:**
- Increase timeout di `python/scraper.py` line ~30
- Increase delay di `python/__main__.py` line ~100
- Retry command kemudian

---

## 📝 Notes

### Data Format Compatibility

Format JSON kompatible dengan:
- Web display yang sudah jalan
- Master index untuk search
- Individual files untuk detail page
- Mudah export ke database later

### Paraphrasing Strategy

Synopsis di-paraphrase jadi bahasa gaul biar:
- Beda dari original (avoid plagiarism detection)
- Lebih casual & engaging untuk user
- Still retain original meaning

Simple implementation: regex replacements + casual markers
Bisa upgrade ke: OpenAI API / Indonesian paraphraser

### Image URLs Only

Images stored sebagai URLs, bukan downloaded, karena:
- ✅ Hemat disk space (crucial untuk large collection)
- ✅ Always fresh images (no caching issues)
- ✅ Reduce bandwidth (lazy load di web)
- ✅ Legal issues (not storing copyrighted images)

Web display: `<img src="image-url-from-json" />`

---

## 📞 Support

Error/issue? Check:
1. Python version (should be 3.8+)
2. Internet connection
3. Komiku.org status (sometimes down)
4. Log output dari scraper (punya INFO & ERROR messages)

Tambah logging:
```python
# Di __main__.py atau scraper.py
logging.basicConfig(level=logging.DEBUG)  # More verbose
```

### 3. Scrape dengan Limit:
```bash
python -m python batch-scrape --limit 20
```

### 4. Scrape by Genre:
```bash
python -m python batch-scrape --genre action --limit 10
```

---

## 📊 Cara Kerja

1. **List Scraper** (`scraper_komiku.py`)
   - Buka `https://komiku.org/pustaka/?tipe=manga`
   - Scroll infinite sampai end of page
   - Extract semua manga link dari halaman
   - Default dapat 120+ komik

2. **Detail Scraper** 
   - Untuk setiap komik, buka detail page
   - Extract: Judul, Cover, Sinopsis, Genre, Chapter List
   - Save ke `data/{slug}.json`

3. **Chapter Scraper**
   - Untuk setiap chapter, extract image URLs
   - Hanya copy link (hotlink), tidak download file

4. **HTML Generator**
   - Convert JSON ke HTML pages
   - Match GreedyComicHub UI/UX
   - Ready untuk di-publish

---

## 📁 Output Structure

```
data/
├── index.json                 # Master index semua komik
├── dandadan.json              # Detail per komik
├── lostend.json
└── ...50+ more

/
├── list_comics.html           # List halaman
├── manga-dandadan.html        # Detail pages
├── manga-lostend.html
└── ...50+ more
```

---

## 🎯 Hasil Test Verifikasi

### Test 1: Single Manga
```
✓ dandadan: 225 chapters extracted
✓ lostend: 34 chapters extracted  
✓ Metadata (cover, genres, etc) all correct
```

### Test 2: Batch Scraping
```
✓ Found 120 manga di list page
✓ Successfully scraped 3 manga (limit test)
✓ Proper skip/resume handling
```

### Test 3: HTML Generation
```
✓ Generated 48 manga pages
✓ Generated 1 master list page
✓ All files created successfully
```

---

## ⚙️ Technical Details

- **Engine**: Selenium WebDriver + Chrome Headless
- **CSS Selectors**: Multiple fallbacks untuk robustness
- **Timeouts**: 15 detik untuk page load
- **Scroll**: Automatic infinite scroll detection
- **Rate Limiting**: 0.5s delay antar request
- **User-Agents**: Random rotation untuk avoid blocks

---

## 🔧 Customization

### Scrape Specific Genre:
```bash
python -m python batch-scrape --genre horror --limit 5
```

### Resume dari Komik Tertentu:
```bash
python -m python batch-scrape --resume dandadan
```

### Ubah Limit Scroll:
Edit `python/scraper_komiku.py` → ubah `max_scrolls` value

---

## 📌 Notes

- Semua image adalah hotlinks (URL, bukan file)
- Auto-update index.json setiap kali scrape
- Supports semua tipe: Manga, Manhua, Manhwa
- Genre filtering via `/genre/{genre}/` path
- Full error handling dan logging

---

**Version**: 1.0  
**Last Updated**: 27 January 2026  
**Status**: Production Ready ✅
