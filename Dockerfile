FROM n8nio/n8n

USER root
ENV PYTHONUNBUFFERED=1

# 安裝必要的套件，包括 tzdata 和 ntpd
RUN apk add --update --no-cache python3 py3-pip curl ffmpeg tzdata busybox-extras

# 設定時區為 UTC（或替換為你需要的時區，例如 Asia/Taipei）
ENV TZ=UTC
RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 同步時間（使用 busybox 的 ntpd 工具）
RUN ntpd -d -q -n -p pool.ntp.org || true

# 建立 Python 虛擬環境
RUN python3 -m venv /opt/venv \
    && chown -R node:node /opt/venv

USER node
ENV PATH="/opt/venv/bin:$PATH"
