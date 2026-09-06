"""
GitHub Actions 실행 시, 이 채널에 해당하는 Secrets
(예: PSYCHOLOGY_CLIENT_SECRET_B64, PSYCHOLOGY_TOKEN_B64)를 찾아서
credentials/ 폴더에 실제 파일로 복원합니다.

사용: python scripts/restore_credentials.py <channel_id>
환경변수 SECRETS_JSON에 ${{ toJSON(secrets) }} 결과가 들어있어야 합니다.
"""
import base64
import json
import os
import sys


def main():
    if len(sys.argv) < 2:
        print("사용법: python restore_credentials.py <channel_id>", file=sys.stderr)
        sys.exit(1)

    channel_id = sys.argv[1]
    prefix = channel_id.upper().replace("-", "_")

    secrets_json = os.environ.get("SECRETS_JSON")
    if not secrets_json:
        print("SECRETS_JSON 환경변수가 없습니다.", file=sys.stderr)
        sys.exit(1)

    secrets = json.loads(secrets_json)
    client_secret_b64 = secrets.get(f"{prefix}_CLIENT_SECRET_B64")
    token_b64 = secrets.get(f"{prefix}_TOKEN_B64")

    if not client_secret_b64 or not token_b64:
        print(
            f"오류: '{prefix}_CLIENT_SECRET_B64' 또는 '{prefix}_TOKEN_B64' "
            f"Secret이 등록되어 있지 않습니다. 관리 프로그램에서 이 채널의 "
            f"유튜브 계정을 먼저 연결해주세요.",
            file=sys.stderr,
        )
        sys.exit(1)

    os.makedirs("credentials", exist_ok=True)
    with open(f"credentials/client_secret_{channel_id}.json", "wb") as f:
        f.write(base64.b64decode(client_secret_b64))
    with open(f"credentials/token_{channel_id}.json", "wb") as f:
        f.write(base64.b64decode(token_b64))

    print(f"'{channel_id}' 채널 인증 파일 복원 완료")


if __name__ == "__main__":
    main()
