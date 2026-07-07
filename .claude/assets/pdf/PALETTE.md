# 공통 PDF/문서 색 표준 (PALETTE)

문서(PDF·도해)에서 공통으로 쓰는 색 토큰의 **단일 출처**다. PDF 테마는 `style.html`, 다이어그램(mermaid)은 `mermaid.json`이 이 값을 반영한다.

> **정본 기준:** 라이프플래닛 그린(`#00A862`) 계열. UI 화면(`docs/.../ui/04_design_direction.md` §3 컬러 팔레트)과 동일 토큰을 쓴다.
> 헥스값은 라이프플래닛 브랜드 톤 **제안값**이며, 공식 브랜드 가이드 수령 후 이 파일·`style.html`·`mermaid.json`에서 일괄 교체한다(미결).

## 토큰

| 용도 | 토큰 | 헥스 | 적용처(PDF) |
|------|------|------|-------------|
| Primary | 라이프플래닛 그린 | `#00A862` | h1 밑줄, h2 좌측 바, blockquote 바, 간트 태스크 바 |
| Primary Deep | 딥 그린 | `#00713F` | h2 글자, 링크, 간트 태스크 외곽선 |
| Secondary | 라이트 그린 | `#E6F6EE` | 표 헤더·코드 배경 |
| Secondary Soft | 소프트 그린 | `#F0FAF4` | blockquote 배경 |
| Neutral | 차콜 | `#1F2937` | 본문·강조 텍스트 |
| Neutral Light | 오프 화이트 | `#F8FAFC` | 간트 섹션 배경 |
| Border | 라이트 그레이 | `#E5E7EB` | 표 테두리, hr, 그리드 |
| Meta | 그레이 | `#6B7280` | 메타·캡션 |
| Danger | 레드 | `#E53E3E` | today 라인·위험 강조 |
| Warning | 앰버 | `#D97706` | em 강조, note 박스 테두리 |
| Warning BG | 라이트 앰버 | `#FFFBEB` | note 박스 배경 |
| Warning Text | 딥 앰버 | `#92400E` | note 박스 글자 |

## 브랜드 분리 (병합 금지)

- **뤼튼 자체 브랜드 그린 `#0F5647`** (제안서 슬라이드 `kyobo-salesbot-proposal/`)은 **뤼튼의 정체성**이라 본 문서 테마와 목적이 다르다. 클라이언트(라이프플래닛) 문서 색과 **합치지 않는다.**
- 과거 PDF에서 쓰던 근사 초록 `#2f855a`는 본 표준(`#00A862`)으로 대체됐다.

## 사용법

```bash
.claude/scripts/make_pdf.sh <입력.md> <출력.pdf> "[문서 제목]"
```

`make_pdf.sh`가 ① md 안의 ```mermaid 블록을 `mermaid.json` 테마로 PNG 렌더해 치환하고 ② `style.html`을 주입해 pandoc→weasyprint로 PDF를 만든다.
