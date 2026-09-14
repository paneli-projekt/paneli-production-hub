-- Paneli Production Hub — shema baze (SQLite), verzija 3 (13. 9. 2026.; v1 = 12. 9., v2 = 13. 9.)
-- Migracije starijih baza: hub/db.py MIGRACIJE (v2: kupac adresa/OIB, nalog_materijal ulazni naziv; v3: vrsta kupca i subjekt za Pantheon, D-48).
-- Model po docs/04 §2, dopune po docs/10 §4 (događaji, rokovi, rezervacije, narudžbenice, operacije) i D-40 (rabat, ponuda iz Huba).
-- Korak 1 kralježnice puni samo šifrarnike (pantheon_ident, materijal, materijal_alias, winstore_ploca, traka, traka_alias,
-- materijal_traka); ostale tablice postoje od početka da ih kasniji koraci ne moraju mijenjati (D-12, D-42).
-- Konvencije: nazivi tablica i stupaca hrvatski bez dijakritike, datumi ISO tekst (YYYY-MM-DD[THH:MM:SS]), novac REAL u EUR.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS shema_verzija (
    verzija     INTEGER PRIMARY KEY,
    primijenjeno TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS postavke (                 -- konfiguracija bez koda (kerf, mape, e-mail…)
    kljuc       TEXT PRIMARY KEY,
    vrijednost  TEXT,
    opis        TEXT
);

CREATE TABLE IF NOT EXISTS korisnik (                 -- Ivana, Goran, Sanela, voditelj, Igor (04 §3: samo ime + dnevnik, bez prava u fazi 1)
    id          INTEGER PRIMARY KEY,
    oznaka      TEXT NOT NULL UNIQUE,                  -- IVANA, GORAN, SANELA, VP, IGOR
    ime         TEXT,
    uloga       TEXT,                                  -- ured | nabava | voditelj | admin
    aktivan     INTEGER NOT NULL DEFAULT 1
);

-- ---------------------------------------------------------------- Pantheon (čita se iz izvoza ph_*.csv, D-06)
CREATE TABLE IF NOT EXISTS pantheon_ident (            -- kopija šifrarnika identa: cijene za obračun (D-40: cijena se u Hubu ne mijenja)
    ident           TEXT PRIMARY KEY,                  -- IV000090, TR001254, US000002, OK001850, RP000136…
    naziv           TEXT NOT NULL,
    klasif          TEXT,                              -- acClassif (IV, TR, OK, US, RP, PR, AP…)
    kod             TEXT,                              -- acCode (šifra dobavljača / dekora)
    dobavljac       TEXT,
    jm              TEXT,                              -- M2, M, KOM, KPT…
    cijena_prodajna REAL,                              -- anSalePrice (s PDV-om)
    cijena_neto     REAL,                              -- anRTPrice = anSalePrice / 1,25 (D-40)
    pdv             REAL,
    aktivan         INTEGER NOT NULL DEFAULT 1,
    azurirano       TEXT NOT NULL                      -- datum/vrijeme uvoza
);
CREATE INDEX IF NOT EXISTS ix_pantheon_ident_klasif ON pantheon_ident (klasif);

CREATE TABLE IF NOT EXISTS kupac (                    -- iz Pantheon subjekata (D-12, tHE_SetSubj acBuyer = T) + rabat po kupcu u Hubu (D-40)
    id                INTEGER PRIMARY KEY,
    pantheon_subjekt  TEXT UNIQUE,                     -- acSubject (ključ u Pantheonu); NULL = kupac otvoren u Hubu (fizička osoba, D-48)
    izvor             TEXT NOT NULL DEFAULT 'pantheon',-- pantheon | hub
    vrsta             TEXT,                            -- tvrtka | obrt | krajnji (fizička osoba) | zajednicki (subjekt 'Krajnji kupac') — nosi zadani rabat
    pantheon_subjekt_racun TEXT,                       -- subjekt kome u Pantheonu ide ponuda / račun (eSlog BY): vlastiti ili 'Krajnji kupac' (D-48)
    naziv             TEXT NOT NULL,                   -- acSubject / ime i prezime (kako ga ured zove)
    naziv_puni        TEXT,                            -- acName2
    adresa            TEXT,                            -- acAddress
    posta             TEXT,                            -- acPost: HR-31000
    mjesto            TEXT,                            -- iz ph_poste.csv po acPost
    drzava            TEXT,
    oib               TEXT,                            -- acPIN
    fizicka_osoba     INTEGER NOT NULL DEFAULT 0,      -- acNaturalPerson
    email             TEXT,                            -- Hub (Pantheon kontakti nisu u izvozu — D-40 preduvjet 1)
    telefon           TEXT,
    rabat_materijal   REAL,                            -- % za materijal + okov + ostalo (npr. 15) — samo u Hubu (D-40)
    rabat_usluge      REAL,                            -- % za rezanje i kantiranje (npr. 20)
    dani_placanja     INTEGER,                         -- anDaysForPayment (u Pantheonu gotovo nikad popunjeno) — ured može upisati u Hubu
    napomena          TEXT,
    aktivan           INTEGER NOT NULL DEFAULT 1,
    pantheon_azurirano TEXT,                           -- zadnji uvoz iz ph_subjekti.csv
    trazi             TEXT                             -- normalizirani tekst za pretragu (naziv, puni naziv, adresa, pošta, mjesto, OIB)
);

-- ---------------------------------------------------------------- šifrarnik materijala (ploče) — D-24, D-31, D-37
CREATE TABLE IF NOT EXISTS materijal (
    id              INTEGER PRIMARY KEY,
    pantheon_ident  TEXT NOT NULL UNIQUE REFERENCES pantheon_ident (ident),
    naziv_pantheon  TEXT NOT NULL,                     -- IVERAL BIJELI NK W908 ST2 18 MM
    naziv_kratki    TEXT,                              -- IV BIJELI NK 18 (kako ga pišu PW / PPNEST / nalog)
    vrsta           TEXT NOT NULL,                     -- IV | MDF | PVC | AK | HPL | CP | SP | RP | ZO | OST
    obitelj_rp      TEXT,                              -- radna (600) | stola (900) | zidna (640) — samo za RP/ZO (D-37)
    debljina        REAL,                              -- mm
    dekor           TEXT,                              -- riječi dekora bez vrste/koda/debljine: BIJELI NK
    dekor_kod       TEXT,                              -- W908 ST2, K2665 AI, 27045 OF, VSM-06…
    winstore_kod    TEXT,                              -- MaterialCode u Winstoreu: W908ST2-18 (ključ za bNest CSV, D-24)
    ploca_L         REAL,                              -- zadana dimenzija ploče iz šifrarnika, ne po nalogu (D-24)
    ploca_W         REAL,
    god             INTEGER,                           -- 1 = materijal s godom (Winstore Grain), 0 = bez, NULL = nepoznato
    sirina_rp       INTEGER,                           -- 600 / 640 / 900 za radne, zidne i ploče stola
    samo_cijela     INTEGER NOT NULL DEFAULT 0,        -- dekor po narudžbi → prodaje se samo cijela ploča (D-37b)
    aktivan         INTEGER NOT NULL DEFAULT 1,
    trazi           TEXT,                              -- normalizirani tekst za pretragu (naziv u oba pisanja, ident, Winstore kod)
    napomena        TEXT
);
CREATE INDEX IF NOT EXISTS ix_materijal_vrsta ON materijal (vrsta, debljina);
CREATE INDEX IF NOT EXISTS ix_materijal_winstore ON materijal (winstore_kod);

CREATE TABLE IF NOT EXISTS materijal_alias (          -- kako materijal pišu PW, PPNEST, kupci, Corpus → materijal (D-24, 08 §3.3)
    id           INTEGER PRIMARY KEY,
    alias        TEXT NOT NULL,                        -- izvorni tekst
    alias_norm   TEXT NOT NULL UNIQUE,                 -- normalizirani tekst (nazivi.norm)
    materijal_id INTEGER NOT NULL REFERENCES materijal (id),
    izvor        TEXT,                                 -- skill krojna-ponuda | cpo | cpw | csv | winstore | ponuda 26-010-… | rucno
    potvrdio     TEXT,                                 -- oznaka korisnika koji je potvrdio (NULL = automatski)
    kada         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS winstore_ploca (           -- Winstore inventar (XML izvoz operatera, I-12): cijele ploče za nesting (D-02)
    id             INTEGER PRIMARY KEY,
    kod            TEXT NOT NULL,                      -- Code: W908ST2-18-2800-2070
    materijal_kod  TEXT NOT NULL,                      -- MaterialCode: W908ST2-18
    opis           TEXT,                               -- MaterialDescription
    L              REAL, W REAL, debljina REAL,
    god            INTEGER,
    kom_ukupno     INTEGER NOT NULL DEFAULT 0,
    kom_interno    INTEGER NOT NULL DEFAULT 0,
    kom_eksterno   INTEGER NOT NULL DEFAULT 0,
    drop_ploca     INTEGER NOT NULL DEFAULT 0,         -- Drop = ostatak (restl u Winstoreu)
    izvoz          TEXT NOT NULL,                      -- naziv/datum izvoza (11092026.XML)
    materijal_id   INTEGER REFERENCES materijal (id)   -- veza na Pantheon materijal (NULL = nije povezano)
);
CREATE INDEX IF NOT EXISTS ix_winstore_kod ON winstore_ploca (materijal_kod);

-- ---------------------------------------------------------------- šifrarnik traka — D-20, D-31
CREATE TABLE IF NOT EXISTS traka (
    id                 INTEGER PRIMARY KEY,
    pantheon_ident     TEXT NOT NULL UNIQUE REFERENCES pantheon_ident (ident),
    naziv              TEXT NOT NULL,                  -- ABS 1/22 BIJELI NK
    vrsta              TEXT NOT NULL,                  -- ABS | PVC | MEL | OST
    debljina           REAL,                           -- 0,5 / 1 / 1,3 / 2
    sirina             INTEGER,                        -- 22 / 29 / 44 / 66…
    klasa              TEXT,                           -- "1/22", "0,5/22", "2/44" — ključ za D-31 i usluge kantiranja
    dekor              TEXT,                           -- riječi dekora: BIJELI NK, JELA CLAY
    kod                TEXT,                           -- acCode dobavljača (624B…)
    dobavljac          TEXT,
    regal_traka_ident  TEXT,                           -- ident u aplikaciji regal-traka (isti Pantheon ident)
    aktivan            INTEGER NOT NULL DEFAULT 1,
    trazi           TEXT                               -- normalizirani tekst za pretragu
);
CREATE INDEX IF NOT EXISTS ix_traka_klasa ON traka (klasa);

CREATE TABLE IF NOT EXISTS traka_alias (              -- oznaka trake u nalogu → TR ident; uz materijal (ISTI) ili općenito
    id           INTEGER PRIMARY KEY,
    alias        TEXT NOT NULL,
    alias_norm   TEXT NOT NULL,
    materijal_id INTEGER REFERENCES materijal (id),    -- NULL = vrijedi za sve materijale
    traka_id     INTEGER NOT NULL REFERENCES traka (id),
    izvor        TEXT,
    potvrdio     TEXT,
    kada         TEXT NOT NULL,
    UNIQUE (alias_norm, materijal_id)
);

CREATE TABLE IF NOT EXISTS materijal_traka (          -- zadane trake po materijalu i klasi (D-31): MEL-ISTI → 0,5/22, ABS-ISTI → 1/22, ABS-ISTI 2mm → 2/22
    materijal_id INTEGER NOT NULL REFERENCES materijal (id),
    klasa        TEXT NOT NULL,                        -- "0,5/22" | "1/22" | "2/22" | "1/44" …
    traka_id     INTEGER NOT NULL REFERENCES traka (id),
    izvor        TEXT,
    potvrdio     TEXT,
    kada         TEXT NOT NULL,
    PRIMARY KEY (materijal_id, klasa)
);

-- ---------------------------------------------------------------- nalog (korak 2+; definirano sada, D-33, D-35, D-40, D-42)
CREATE TABLE IF NOT EXISTS nalog (
    id                   INTEGER PRIMARY KEY,
    broj                 TEXT NOT NULL UNIQUE,         -- Hub broj: 2026-02823 (D-33)
    naziv                TEXT NOT NULL,                -- KUPAC_NAZIV_BROJ: HUMER_OMIS_2823
    kupac_id             INTEGER REFERENCES kupac (id),
    vrsta                TEXT NOT NULL DEFAULT 'usluga',   -- usluga | vlastita_proizvodnja (D-30)
    izvor                TEXT,                         -- kupac_ppw | kupac_excel | kupac_rukopis | corpus | rucno
    corpus_projekt       TEXT,
    status               TEXT NOT NULL DEFAULT 'unos', -- unos | ponuda | potvrdjeno | skladiste | pila_nesting | proizvodnja | zatvoren (D-35)
    datum                TEXT NOT NULL,
    izradio_id           INTEGER REFERENCES korisnik (id),
    kerf                 REAL NOT NULL DEFAULT 16,     -- za obračun; u CPO ide 5 (D-21)
    ponuda_pantheon      TEXT,                         -- 26-010-002823 — tek nakon potvrde kupca (D-40)
    rabat_materijal      REAL,                         -- kopija s kupca u trenutku ponude (D-40)
    rabat_usluge         REAL,
    rok_obecan           TEXT,                         -- službeni rok (ured pri potvrdi, 10 §6)
    rok_kupca            TEXT,                         -- napomena
    prioritet            TEXT,
    potvrda_kupca_datum  TEXT,
    potvrda_kupca_nacin  TEXT,                         -- mail | telefon | osobno
    potvrdio_id          INTEGER REFERENCES korisnik (id),
    napomena             TEXT
);

CREATE TABLE IF NOT EXISTS ponuda_verzija (           -- verzije ponude iz Huba (D-40): svaka poslana verzija čuva PDF i tekst maila
    id           INTEGER PRIMARY KEY,
    nalog_id     INTEGER NOT NULL REFERENCES nalog (id),
    verzija      INTEGER NOT NULL,
    status       TEXT NOT NULL DEFAULT 'nacrt',        -- nacrt | poslana | potvrdjena | zamijenjena
    iznos_neto   REAL, iznos_pdv REAL,
    poslano_kada TEXT, poslao_id INTEGER REFERENCES korisnik (id), poslano_na TEXT,
    pdf_putanja  TEXT, mail_tekst TEXT,
    eslog_putanja TEXT, eslog_poslan TEXT,
    UNIQUE (nalog_id, verzija)
);

CREATE TABLE IF NOT EXISTS nalog_materijal (
    id             INTEGER PRIMARY KEY,
    nalog_id       INTEGER NOT NULL REFERENCES nalog (id),
    materijal_id   INTEGER REFERENCES materijal (id),  -- NULL dok materijal nije prepoznat / potvrđen (provjeri = 1)
    naziv_ulaz     TEXT,                               -- kako je pisalo u CPW / CSV / Excelu (za potvrdu i alias, D-32)
    debljina_ulaz  REAL,
    winstore_kod_ulaz TEXT,                            -- SIFRA MAT iz PPNEST CSV-a
    provjeri       INTEGER NOT NULL DEFAULT 0,         -- 1 = materijal nije siguran (za potvrdu)
    put            TEXT,                               -- pila | nesting (voditelj potvrđuje, D-34)
    put_prijedlog  TEXT,
    god            INTEGER,
    ploca_L        REAL, ploca_W REAL,                 -- override (restl!)
    traka_zadana   TEXT NOT NULL DEFAULT 'ABS-ISTI',   -- izbornik iznad daske: MEL-ISTI | ABS-ISTI | ABS-ISTI 2mm (D-31, D-36)
    status_opt     TEXT,
    napomena       TEXT,
    rb             INTEGER                             -- redoslijed u nalogu
);

CREATE TABLE IF NOT EXISTS element (
    id                  INTEGER PRIMARY KEY,
    nalog_materijal_id  INTEGER NOT NULL REFERENCES nalog_materijal (id),
    rb                  INTEGER NOT NULL,
    hub_uid             TEXT,                          -- stabilan ID (rezerviran, I-04)
    naziv               TEXT,
    L                   REAL NOT NULL, W REAL NOT NULL, kom INTEGER NOT NULL,
    god                 TEXT,                          -- H | V | NULL
    gotova_mjera        TEXT,
    rub1_traka_id INTEGER REFERENCES traka (id), rub1_kod TEXT,   -- redoslijed duža1, kraća1, duža2, kraća2 (04 §5.1)
    rub2_traka_id INTEGER REFERENCES traka (id), rub2_kod TEXT,
    rub3_traka_id INTEGER REFERENCES traka (id), rub3_kod TEXT,
    rub4_traka_id INTEGER REFERENCES traka (id), rub4_kod TEXT,
    obrada              TEXT, program1 TEXT, program2 TEXT, ljepljenje TEXT,
    napomena            TEXT,                          -- prvih 14 znakova ide na etiketu (D-38)
    cix_ime             TEXT, cix_izvor TEXT,          -- hub | corpus (D-29)
    obrada_json         TEXT,
    cjelina             TEXT, pozicija TEXT,           -- iz Corpusa (08 §4)
    izvor               TEXT,                          -- cpw | excel | rukopis | rucno | corpus
    provjeri            INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS okov_stavka (
    id             INTEGER PRIMARY KEY,
    nalog_id       INTEGER NOT NULL REFERENCES nalog (id),
    pantheon_ident TEXT REFERENCES pantheon_ident (ident),
    naziv          TEXT, kom REAL, jm TEXT,
    izvor_tekst    TEXT,                               -- kako je kupac napisao
    status         TEXT NOT NULL DEFAULT 'za_potvrdu'  -- za_potvrdu | potvrdjeno
);

CREATE TABLE IF NOT EXISTS obracun_stavka (
    id             INTEGER PRIMARY KEY,
    nalog_id       INTEGER NOT NULL REFERENCES nalog (id),
    ponuda_verzija_id INTEGER REFERENCES ponuda_verzija (id),
    rb             INTEGER,
    pantheon_ident TEXT NOT NULL REFERENCES pantheon_ident (ident),
    naziv          TEXT, kolicina REAL NOT NULL, jm TEXT,
    cijena         REAL, rabat REAL,                   -- cijena iz Pantheona, rabat po kupcu (D-40)
    grupa          TEXT,                               -- materijal | rezanje | traka | kantiranje | okov | usluga
    pravilo        TEXT,
    nalog_materijal_id INTEGER REFERENCES nalog_materijal (id)
);

CREATE TABLE IF NOT EXISTS optimizacija (
    id                 INTEGER PRIMARY KEY,
    nalog_materijal_id INTEGER NOT NULL REFERENCES nalog_materijal (id),
    engine             TEXT NOT NULL,                  -- PW | bNest | Hub
    nacin              TEXT,                           -- koji je način pobijedio (D-19)
    datum              TEXT NOT NULL,
    broj_ploca         INTEGER, iskoristenje REAL, m2_dijelova REAL, m2_ploca REAL, m2_za_naplatu REAL, rezova INTEGER,
    sheme_json         TEXT,
    dokument_id        INTEGER
);

CREATE TABLE IF NOT EXISTS dokument (
    id        INTEGER PRIMARY KEY,
    nalog_id  INTEGER REFERENCES nalog (id),
    vrsta     TEXT NOT NULL,                           -- cpw_ulaz | cpw_pw | csv | cix | cpo | pnl | pdf_krojna | mno | lbl | ponuda_pdf | eslog | foto | primka
    putanja   TEXT NOT NULL,
    hash      TEXT,
    datum     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dogadjaj (                 -- vremenska crta naloga (D-42, 10 §1)
    id          INTEGER PRIMARY KEY,
    nalog_id    INTEGER NOT NULL REFERENCES nalog (id),
    kada        TEXT NOT NULL,
    tko_id      INTEGER REFERENCES korisnik (id),
    iz_statusa  TEXT, u_status TEXT,
    razlog      TEXT,
    veza        TEXT                                   -- npr. narudzbenica:12, dokument:5
);
CREATE INDEX IF NOT EXISTS ix_dogadjaj_nalog ON dogadjaj (nalog_id, kada);

-- ---------------------------------------------------------------- skladište (D-02) i nabava (D-42)
CREATE TABLE IF NOT EXISTS ploca_stanje (             -- Hub skladište cijelih ploča (pila-materijali); nesting-ploče čita Winstore
    id            INTEGER PRIMARY KEY,
    materijal_id  INTEGER NOT NULL REFERENCES materijal (id),
    lokacija      TEXT,
    kom           INTEGER NOT NULL DEFAULT 0,
    zadnja_inventura TEXT
);

CREATE TABLE IF NOT EXISTS restl (
    id            INTEGER PRIMARY KEY,
    materijal_id  INTEGER NOT NULL REFERENCES materijal (id),
    L REAL NOT NULL, W REAL NOT NULL,
    lokacija      TEXT, qr TEXT,
    izvor         TEXT,                                -- nalog_materijal:id | rucno | excel_v3
    status        TEXT NOT NULL DEFAULT 'slobodan',    -- slobodan | rezerviran | potrosen
    datum         TEXT
);

CREATE TABLE IF NOT EXISTS rezervacija (              -- raspoloživo = fizičko − rezervirano + naručeno (D-42)
    id                 INTEGER PRIMARY KEY,
    nalog_materijal_id INTEGER NOT NULL REFERENCES nalog_materijal (id),
    restl_id           INTEGER REFERENCES restl (id),
    ploca_stanje_id    INTEGER REFERENCES ploca_stanje (id),
    winstore_kod       TEXT,
    kom                REAL NOT NULL,
    status             TEXT NOT NULL DEFAULT 'rezervirano',  -- rezervirano | izdano | potroseno | oslobodjeno
    datum              TEXT NOT NULL, korisnik_id INTEGER REFERENCES korisnik (id),
    izdao_id           INTEGER REFERENCES korisnik (id), izdano_kada TEXT
);

CREATE TABLE IF NOT EXISTS narudzbenica (             -- modul nabava (D-42): nastaje u Hubu, zatvara se iz eSlog primke
    id          INTEGER PRIMARY KEY,
    broj        TEXT NOT NULL UNIQUE,                  -- N-2026-043
    dobavljac   TEXT NOT NULL,                         -- Pantheon subjekt
    datum       TEXT NOT NULL,
    narucio_id  INTEGER REFERENCES korisnik (id),
    ocekivano   TEXT,
    status      TEXT NOT NULL DEFAULT 'nacrt',         -- nacrt | poslana | djelomicno | zaprimljena
    poslano_kada TEXT,
    napomena    TEXT
);

CREATE TABLE IF NOT EXISTS narudzbenica_st (
    id                 INTEGER PRIMARY KEY,
    narudzbenica_id    INTEGER NOT NULL REFERENCES narudzbenica (id),
    pantheon_ident     TEXT NOT NULL REFERENCES pantheon_ident (ident),
    naziv              TEXT, kom REAL NOT NULL, jm TEXT, dimenzija TEXT,
    nalog_materijal_id INTEGER REFERENCES nalog_materijal (id),   -- NULL = zaliha unaprijed
    zaprimljeno_kom    REAL NOT NULL DEFAULT 0,
    primka_ref         TEXT
);

CREATE TABLE IF NOT EXISTS operacija (                -- jedinica praćenja = nalog × materijal × stroj (D-42/6); status upisuje praćenje, ne Hub
    id                 INTEGER PRIMARY KEY,
    nalog_id           INTEGER NOT NULL REFERENCES nalog (id),
    nalog_materijal_id INTEGER REFERENCES nalog_materijal (id),   -- NULL = operacija cijelog naloga (pakiranje, okov, isporuka)
    stroj              TEXT NOT NULL,                  -- pila | nesting | rover | kanterica | cnc | ljepljenje | pakiranje
    kolicina           REAL, jm TEXT,
    detalj_json        TEXT
);

CREATE TABLE IF NOT EXISTS dnevnik (                  -- audit trail (04 §2) + zapisi poziva modula ai (D-15)
    id           INTEGER PRIMARY KEY,
    kada         TEXT NOT NULL,
    tko          TEXT,
    entitet      TEXT NOT NULL,
    id_entiteta  TEXT,
    sto          TEXT NOT NULL,
    detalji      TEXT
);

-- ---------------------------------------------------------------- početni podaci
INSERT OR IGNORE INTO korisnik (oznaka, ime, uloga) VALUES ('IVANA', 'Ivana', 'ured'), ('GORAN', 'Goran', 'ured'), ('SANELA', 'Sanela', 'nabava'),
    ('VP', 'Voditelj proizvodnje', 'voditelj'), ('IGOR', 'Igor', 'admin'), ('UVOZ', 'Automatski uvoz', 'sustav'), ('WEB', 'Neprijavljeni korisnik', 'sustav');
INSERT OR IGNORE INTO postavke (kljuc, vrijednost, opis) VALUES
    ('kerf', '16', 'širina reza za obračun (D-21); u CPO ide 5'),
    ('rabat_materijal_zadano', '15', 'zadani rabat novog kupca — materijal, okov, ostalo (D-40)'),
    ('rabat_usluge_zadano', '20', 'zadani rabat novog kupca — rezanje i kantiranje (D-40)'),
    ('brojac_naloga_pocetak', '1', 'prvi broj naloga u godini kad brojač još ne postoji (Igor može podesiti, npr. 3300)'),
    ('krajnji_kupac_subjekt', 'Krajnji kupac', 'Pantheon subjekt na koji idu ponude / računi fizičkih osoba koje Hub vodi sam (D-48)'),
    ('rabat_krajnji_materijal', '0', 'zadani rabat krajnjeg kupca (fizičke osobe) — materijal, okov, ostalo (D-48)'),
    ('rabat_krajnji_usluge', '0', 'zadani rabat krajnjeg kupca — rezanje i kantiranje (D-48)');
