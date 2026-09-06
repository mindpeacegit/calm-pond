# 쇼츠 자동 생성 저장소 (관리 프로그램에서 자동 구성됨)

이 저장소는 shorts_manager 관리 프로그램이 자동으로 채널을 추가/관리합니다.
- `channels/*.json`: 채널별 설정 (주제, 톤, TTS 목소리 등)
- `.github/workflows/daily_upload.yml`: channels/ 폴더를 자동으로 읽어 채널마다 매일 실행
- Secrets: `{채널ID}_CLIENT_SECRET_B64`, `{채널ID}_TOKEN_B64` (관리 프로그램에서 자동 등록)

직접 수정하지 마시고, 로컬의 shorts_manager 프로그램에서 관리해주세요.
