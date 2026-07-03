# 논문/포스터 삽입용 링크 문구 & QR 코드 안내

배포 URL이 확정되면 아래 `<https://YOUR-APP-NAME.streamlit.app>` 부분을
실제 주소로 교체해서 사용한다.

## 1) 논문 본문 삽입용 문장

**국문 (본문/각주)**

> 본 논문에서 제안한 SafeGuard 시스템의 시뮬레이션 결과는 아래 웹
> 데모에서 별도 설치 없이 직접 확인할 수 있다: `<https://YOUR-APP-NAME.streamlit.app>`
> (본 데모는 output-level virtual sensor simulation과 추정 전력 모델
> 기반이며, 실측값이 아님에 유의한다.)

**국문 (각주/부록, 짧은 버전)**

> Live demo: `<https://YOUR-APP-NAME.streamlit.app>`

**영문 (International submission 대비)**

> An interactive web demo of the SafeGuard TwinLab Agent simulator
> (no installation required) is available at:
> `<https://YOUR-APP-NAME.streamlit.app>`. Note that sensor signals are
> output-level virtual simulations and power values are estimates, not
> hardware measurements.

## 2) Figure/QR 캡션 문구

**국문**

> Figure N. SafeGuard TwinLab Agent 웹 데모 QR 코드. 스캔 시
> `<https://YOUR-APP-NAME.streamlit.app>`으로 연결되며, 별도 설치 없이
> 브라우저에서 시뮬레이션을 직접 조작할 수 있다.

**영문**

> Figure N. QR code linking to the SafeGuard TwinLab Agent interactive
> web demo (`<https://YOUR-APP-NAME.streamlit.app>`). No local
> installation is required to explore the simulator.

## 3) QR 코드 생성 방법

배포 URL이 확정된 뒤 아래 명령으로 실제 QR 코드 PNG를 생성한다
(사전에 URL이 없는 상태에서 QR을 미리 만들면 스캔 시 존재하지 않는
링크로 연결되므로, **반드시 배포 완료 후** 실행한다).

```bash
python -m pip install "qrcode[pil]"
python scripts/generate_qr_code.py https://YOUR-APP-NAME.streamlit.app --out docs/qr_code.png
```

생성된 `docs/qr_code.png`를 논문/포스터에 삽입하면 된다.

## 4) 체크리스트

- [ ] Streamlit Cloud 배포 완료, 실제 URL 확보
- [ ] 위 1)~2)의 `<https://YOUR-APP-NAME.streamlit.app>`을 실제 URL로 전체 교체
- [ ] `python scripts/generate_qr_code.py <실제 URL>`로 `docs/qr_code.png` 생성
- [ ] 논문/포스터에 QR 코드 이미지와 캡션 삽입
- [ ] README.md 상단 배지의 URL도 동일하게 교체 (DEPLOYMENT_CHECKLIST.md 3번 항목)
