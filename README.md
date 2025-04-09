# OBJ to PDF Converter

## Installation

1. Klonen Sie das Repository mit Submodules:
```bash
git clone --recursive https://github.com/damianhunziker/obj_to_pdf.git
cd obj_to_pdf
```

2. Installieren Sie das Paket:
```bash
pip install -e .
```

## Git Submodules Management

### Initial Setup
Wenn Sie das Repository zum ersten Mal klonen, verwenden Sie:
```bash
git clone --recursive https://github.com/damianhunziker/obj_to_pdf.git
```

Falls Sie das Repository bereits ohne Submodules geklont haben:
```bash
git submodule update --init --recursive
```

### Submodules aktualisieren
Um alle Submodules auf den neuesten Stand zu bringen:
```bash
git submodule update --remote --merge
```

Um ein bestimmtes Submodule zu aktualisieren:
```bash
cd obj_to_u3d  # oder u3d_pdf
git pull origin main
cd ..
git add obj_to_u3d  # oder u3d_pdf
git commit -m "Update submodule to latest version"
```

### Submodule-Änderungen committen
Wenn Sie Änderungen in einem Submodule vorgenommen haben:
1. Wechseln Sie in das Submodule-Verzeichnis
2. Committen Sie die Änderungen wie gewohnt
3. Wechseln Sie zurück ins Hauptverzeichnis
4. Committen Sie die neue Submodule-Referenz

```bash
cd obj_to_u3d  # oder u3d_pdf
git add .
git commit -m "Your changes"
git push origin main
cd ..
git add obj_to_u3d  # oder u3d_pdf
git commit -m "Update submodule reference"
git push
```

### Submodule auf bestimmten Commit setzen
Um ein Submodule auf einen bestimmten Commit zu setzen:
```bash
cd obj_to_u3d  # oder u3d_pdf
git checkout <commit-hash>
cd ..
git add obj_to_u3d  # oder u3d_pdf
git commit -m "Set submodule to specific commit"
```

### Submodule entfernen
Um ein Submodule zu entfernen:
```bash
# Submodule deinitialisieren
git submodule deinit -f obj_to_u3d  # oder u3d_pdf

# .git/config Eintrag entfernen
git config -f .git/config --remove-section submodule.obj_to_u3d  # oder u3d_pdf

# .gitmodules Eintrag entfernen
git config -f .gitmodules --remove-section submodule.obj_to_u3d  # oder u3d_pdf

# Submodule-Verzeichnis aus Git entfernen
git rm -f obj_to_u3d  # oder u3d_pdf

# Änderungen committen
git commit -m "Remove submodule"
```

## Projektstruktur
```
obj_to_pdf/
├── obj_to_pdf.py
├── setup.py
├── requirements.txt
├── README.md
├── obj_to_u3d/     (Git Submodule)
└── u3d_pdf/        (Git Submodule)
```

## Verwendung
[Verwendungsanweisungen hier]
