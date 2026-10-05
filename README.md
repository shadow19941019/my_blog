# Day 69 – Blog felhasználókkal (kezdőcsomag)

Ez egy önállóan elkészített, valószínűsíthető kezdőcsomag Angela Yu Python-kurzusának 69. napjához.
Nem kész megoldás: a fontos részek TODO jelöléssel szerepelnek.

## Indítás

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

Nyisd meg: http://127.0.0.1:5000

## Fő feladatok

1. User modell létrehozása és adatbázisba kötése.
2. Regisztráció, egyedi e-mail ellenőrzése, jelszó-hash.
3. Bejelentkezés és kijelentkezés Flask-Login használatával.
4. Védett admin oldalak (`@login_required`).
5. Szerző hozzárendelése a blogbejegyzéshez.
6. Comment modell, kommentűrlap és kapcsolatok.
7. A navigáció és sablonok módosítása a bejelentkezési állapot szerint.

A `main.py`, `forms.py` és a sablonok TODO megjegyzései vezetik a munkát.
