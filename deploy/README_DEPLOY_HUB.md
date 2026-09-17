# Hub na VM 192.168.5.201 (port 8766; 8765 je Knjiga, 8080 Regal traka)

Kod Huba živi na Igorovom PC-u (`CLAUDE_COWORK\Paneli_Production_Hub\30_NOVI_PROGRAM` = Git repo) i na GitHubu. Na VM-u ga NEMA dok se ne kopira —
zato `http://192.168.5.201:8766/` ne odgovara kad uvicorn radi na PC-u (tada je Hub na `http://localhost:8766/` tog PC-a).

1. **Na PC-u**: `deploy\1_KOPIRAJ_HUB_NA_VM.bat` (robocopy na `\\192.168.5.201\c$\Paneli\Hub`, bez .git / __pycache__ / _to_delete).
2. **Na VM-u** (RDP, cmd kao administrator): `C:\Paneli\Hub\deploy\2_VM_HUB_POSTAVI.bat` — pip paketi, firewall 8766 (LAN), start.
3. S drugog računala: `http://192.168.5.201:8766/`.
4. Kad radi: Task Scheduler „Paneli - Hub Server“ → `C:\Paneli\Hub\deploy\HUB_SERVER.bat` (At startup, delay 30 s, restart on failure) — isto kao Knjiga.

Kasniji deploy koda: ponoviti korak 1 (`/XO` ne prepisuje datoteke koje su na VM-u novije, pa `hub.db` s VM-a ostaje) i restartati task.
Baza na VM-u = `C:\Paneli\Hub\hub.db` (prvo kopiranje nosi PC-ovu bazu s probnim nalozima; prije stvarnog rada obrisati probne naloge).

## Ponovno kopiranje nakon izmjena (17. 9. i dalje)

1. Na PC-u: `deploy\1_KOPIRAJ_HUB_NA_VM.bat` — sam zatvori stare veze, prijavi se kao `PANELI-PC\Igor` (lozinka VM korisnika Igor) i robocopy-em prenese samo novije datoteke (`hub.db` na VM-u ostaje ako je noviji).
2. Na VM-u: u prozoru Huba Ctrl+C, pa ponovno `C:\Paneli\Hub\deploy\2_VM_HUB_POSTAVI.bat` (ili `HUB_SERVER.bat`). Baza se sama migrira na novu shemu.
3. Prva prijava: Hub radi bez lozinke dok se u **Postavke → Korisnici i prijava** ne postavi prva lozinka (npr. IGOR, admin); od tada svi ulaze s lozinkom. Zaboravljene lozinke: na VM-u `cd /d C:\Paneli\Hub` pa `py -m hub.korisnici --lozinka IGOR` ili `--iskljuci-prijavu`.
