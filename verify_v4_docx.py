from pathlib import Path

s = Path("review_output_v4/docx_extract.txt").read_text(encoding="utf-8")

checks = [
    "Version: 4.0",
    "2026-06-01 | 张涣化 | 4.0",
    "EQP_MaterialLableReport",
    "REST:POST http://IP:Port/api/EAP_TaskDownload",
    "REST:POST http://IP:Port/api/EQP_CTProcessDataReport",
    '"Message": "EQP_TaskCompleteReport"',
]

bad_checks = [
    "EQP_ InnerOuterBindingReport",
    "EQP_ GetSetOrPcsInfo",
    "EQP_ IcCodeReport",
    "EQP_ InnerGetOuterReport",
    "EAP_ DateTimeSyncCommand",
    "REST:POST http://IP:Port/api/ EAP_InitialDataRequest",
    "EQP_MaterialLabelReport",
]

print("expected")
for item in checks:
    print(item, s.find(item))
print("bad")
for item in bad_checks:
    print(item, s.find(item))
