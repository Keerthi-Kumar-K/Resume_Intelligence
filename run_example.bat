@echo off
python main.py ^
  --ats-excel "C:\path\to\ATS_Result_20260805_162355.xlsx" ^
  --filtered-jd "C:\path\to\Filtered_JDs_20260805_132521.docx" ^
  --threshold 80 ^
  --minimum-score 45 ^
  --limit 5
pause
