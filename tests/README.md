# 검증기 회귀 테스트

워크플로우의 검증 스크립트(`validate_traceability.py`·`consistency_check.py`)를 고칠 때
"정상 문서는 통과시키고, 고의로 깨진 문서는 잡는지"를 자동으로 확인하는 안전망이다.

## 실행

```bash
python3 tests/run_tests.py
```

전부 통과하면 종료코드 0, 하나라도 실패하면 1. `.github/workflows/checks.yml`이 push/PR마다 자동 실행한다.

## 구조

- 의존성 없음(stdlib만). 픽스처는 **임시 디렉터리에 생성 후 정리**하므로 저장소를 건드리지 않는다.
- 케이스는 `run_tests.py`의 `CASES`에 인라인 정의 — 각 케이스는 소형 프로젝트(파일 몇 개)를
  임시 docs로 만들고, 검증기를 `--strict`로 돌려 **종료코드 + 출력 문구**를 대조한다.

## 케이스 추가하는 법

`CASES`에 dict 하나 추가:

```python
dict(name="설명", checker=TRACE 또는 CONSIST, exit=기대종료코드,
     files={"prd/PRD.md": "...", "fnspec/기능명세서.md": "..."},
     contains=["출력에 있어야 할 문구"], absent=["없어야 할 문구"])
```

검증기에 새 검사를 추가하면(예: consistency ⑦처럼) **여기에 정상 1 + 깨진 1 케이스를 같이 추가**한다.
