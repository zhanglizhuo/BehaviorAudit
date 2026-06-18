#!/usr/bin/env bash
#
# download_datasets.sh
# Downloads all seven public datasets from their original sources.
# Usage: bash scripts/download_datasets.sh
#
# Each dataset is placed under datasets/ as expected by the audit framework.
# See README.md for dataset licensing details.

set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATASETS_DIR="$BASE_DIR/datasets"
mkdir -p "$DATASETS_DIR"

echo "==> Downloading datasets to $DATASETS_DIR"

# -------------------------------------------------------
# 1. MM-TBA
#    Not directly downloadable via script.
#    Contact dataset authors or visit:
#    https://doi.org/10.1038/s41597-025-05426-6
# -------------------------------------------------------
echo ""
echo "[1/7] MM-TBA — manual download required"
echo "  URL: https://doi.org/10.1038/s41597-025-05426-6"
echo "  Place the dataset under: $DATASETS_DIR/MM-TBA/"

# -------------------------------------------------------
# 2. Higher Ed (UCI ID 856)
# -------------------------------------------------------
echo ""
echo "[2/7] Higher Ed Students Performance Evaluation (UCI ID 856)"
HIGHER_ED_DIR="$DATASETS_DIR/StudentExam"
mkdir -p "$HIGHER_ED_DIR"
if [ ! -f "$HIGHER_ED_DIR/higher_ed_856.csv" ]; then
    wget -q -O /tmp/higher_ed.zip "https://archive.ics.uci.edu/static/public/856/higher+education+students+performance+evaluation.zip" || curl -sL -o /tmp/higher_ed.zip "https://archive.ics.uci.edu/static/public/856/higher+education+students+performance+evaluation.zip"
    if [ -f /tmp/higher_ed.zip ]; then
        unzip -j -o /tmp/higher_ed.zip "*.csv" -d "$HIGHER_ED_DIR" 2>/dev/null
        rm /tmp/higher_ed.zip
        echo "  -> Downloaded to $HIGHER_ED_DIR/higher_ed_856.csv"
    else
        echo "  !! Download failed. Manual: https://archive.ics.uci.edu/dataset/856/higher+education+students+performance+evaluation"
    fi
else
    echo "  -> Already exists, skipping"
fi

# -------------------------------------------------------
# 3. xAPI-Edu
# -------------------------------------------------------
echo ""
echo "[3/7] xAPI-Edu-Data"
XAPI_DIR="$DATASETS_DIR/xAPI-Edu"
mkdir -p "$XAPI_DIR"
if [ ! -f "$XAPI_DIR/xAPI-Edu-Data.csv" ]; then
    # Kaggle requires authentication; provide fallback URL if available
    wget -q -O "$XAPI_DIR/xAPI-Edu-Data.csv" "https://raw.githubusercontent.com/aljarah/xAPI-Edu-Data/master/xAPI-Edu-Data.csv" 2>/dev/null || \
    echo "  !! Download failed. Manual: https://www.kaggle.com/datasets/aljarah/xAPI-Edu-Data"
    if [ -f "$XAPI_DIR/xAPI-Edu-Data.csv" ] && [ -s "$XAPI_DIR/xAPI-Edu-Data.csv" ]; then
        echo "  -> Downloaded to $XAPI_DIR/xAPI-Edu-Data.csv"
    fi
else
    echo "  -> Already exists, skipping"
fi

# -------------------------------------------------------
# 4. Entrance Exam (UCI ID 582)
# -------------------------------------------------------
echo ""
echo "[4/7] Student Performance on an Entrance Examination (UCI ID 582)"
if [ ! -f "$HIGHER_ED_DIR/student_entrance_582.csv" ]; then
    wget -q -O /tmp/entrance_exam.zip "https://archive.ics.uci.edu/static/public/582/student+performance+on+an+entrance+examination.zip" || curl -sL -o /tmp/entrance_exam.zip "https://archive.ics.uci.edu/static/public/582/student+performance+on+an+entrance+examination.zip"
    if [ -f /tmp/entrance_exam.zip ]; then
        unzip -j -o /tmp/entrance_exam.zip "*.csv" -d "$HIGHER_ED_DIR" 2>/dev/null
        rm /tmp/entrance_exam.zip
        echo "  -> Downloaded to $HIGHER_ED_DIR/student_entrance_582.csv"
    else
        echo "  !! Download failed. Manual: https://archive.ics.uci.edu/dataset/582/student+performance+on+an+entrance+examination"
    fi
else
    echo "  -> Already exists, skipping"
fi

# -------------------------------------------------------
# 5. UCI Student (UCI ID 320)
# -------------------------------------------------------
echo ""
echo "[5/7] UCI Student Performance (UCI ID 320)"
UCI_DIR="$DATASETS_DIR/UCI"
mkdir -p "$UCI_DIR"
if [ ! -f "$UCI_DIR/student-por.csv" ]; then
    wget -q -O /tmp/student.zip "https://archive.ics.uci.edu/static/public/320/student+performance.zip" || curl -sL -o /tmp/student.zip "https://archive.ics.uci.edu/static/public/320/student+performance.zip"
    if [ -f /tmp/student.zip ]; then
        unzip -j -o /tmp/student.zip "*.csv" -d "$UCI_DIR" 2>/dev/null || \
        unzip -j -o /tmp/student.zip "student/student-*" -d "$UCI_DIR" 2>/dev/null
        rm /tmp/student.zip
        echo "  -> Downloaded to $UCI_DIR/"
    else
        echo "  !! Download failed. Manual: https://archive.ics.uci.edu/dataset/320/student+performance"
    fi
else
    echo "  -> Already exists, skipping"
fi

# -------------------------------------------------------
# 6. Student Dropout (UCI ID 697)
# -------------------------------------------------------
echo ""
echo "[6/7] Predict Students Dropout and Academic Success (UCI ID 697)"
DROPOUT_DIR="$DATASETS_DIR/StudentDropout"
mkdir -p "$DROPOUT_DIR"
if [ ! -f "$DROPOUT_DIR/student_dropout.csv" ]; then
    wget -q -O /tmp/dropout.zip "https://archive.ics.uci.edu/static/public/697/predict+students+dropout+and+academic+success.zip" || curl -sL -o /tmp/dropout.zip "https://archive.ics.uci.edu/static/public/697/predict+students+dropout+and+academic+success.zip"
    if [ -f /tmp/dropout.zip ]; then
        unzip -j -o /tmp/dropout.zip "*.csv" -d "$DROPOUT_DIR" 2>/dev/null
        rm /tmp/dropout.zip
        echo "  -> Downloaded to $DROPOUT_DIR/student_dropout.csv"
    else
        echo "  !! Download failed. Manual: https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success"
    fi
else
    echo "  -> Already exists, skipping"
fi

# -------------------------------------------------------
# 7. OULAD
# -------------------------------------------------------
echo ""
echo "[7/7] Open University Learning Analytics Dataset (OULAD)"
OULAD_DIR="$DATASETS_DIR/OULAD"
mkdir -p "$OULAD_DIR"
if [ ! -f "$OULAD_DIR/assessments.csv" ]; then
    wget -q -O /tmp/oulad.zip "https://analyse.kmi.open.ac.uk/open_dataset/download" 2>/dev/null || curl -sL -o /tmp/oulad.zip "https://analyse.kmi.open.ac.uk/open_dataset/download"
    if [ -f /tmp/oulad.zip ] && [ -s /tmp/oulad.zip ]; then
        unzip -j -o /tmp/oulad.zip -d "$OULAD_DIR" 2>/dev/null
        rm /tmp/oulad.zip
        echo "  -> Downloaded to $OULAD_DIR/"
    else
        echo "  !! Download failed. Manual: https://analyse.kmi.open.ac.uk/open_dataset"
    fi
else
    echo "  -> Already exists, skipping"
fi

echo ""
echo "==> Done. Some datasets may require manual download (see messages above)."
echo "    Run 'python3 run_audit.py --dataset uci_student --seeds 0 1' to verify."
