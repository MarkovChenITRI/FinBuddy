# FinBuddy

## Installation

* 取得`searxng-docker`子模組
    ```bash
    git submodule update --init --recursive
    ```
### Searxng
#### 設定
* 修改`searxng-docker/.env`中的瀏覽器使用者資訊
    ```python
    6 SEARXNG_HOSTNAME=<host>
    7 LETSENCRYPT_EMAIL=<email>
    ```

* 修改`searxng-docker/docker-compose.yaml`的IP為`0.0.0.0:8080:8080`
    ```bash
    searxng:
    container_name: searxng
    image: docker.io/searxng/searxng:latest
    restart: unless-stopped
    networks:
      - searxng
    ports:
      - "0.0.0.0:8080:8080"
    ```
* 修改`searxng-docker/searxng/settings.yml`的`secret_key`、`limiter`及`search format`
    ```bash
    search:
    # options available for formats: [html, csv, json, rss]
    formats:
        - html
        - json
    use_default_settings: true
    server:
    # base_url is defined in the SEARXNG_BASE_URL environment variable, see .env and docker-compose.yml
    secret_key: "eadc2e956f1acb06bb648573abe7a54f667533c1b848b48e37c419655e71db5c"  # change this!
    limiter: false  # can be disabled for a private instance
    image_proxy: true
    ```
    * secret_key請按照[官方文件的指引](https://github.com/searxng/searxng-docker/tree/master)於本機生成

#### 啟動(第一個命令列)
* 通過Docker Compose啟動瀏覽器服務
    ```bash
    cd searxng-docker
    docker compose up -d
    ```

### FinBuddy-MCP-Server
#### 設定
* 取得`FinBuddy-MCP-Server`及子模組
    ```bash
    git clone https://github.com/MarkovChenITRI/FinBuddy-MCP-Server.git

    cd FinBuddy-MCP-Server
    git submodule update --init --recursive
    ```

* 創建虛擬環境並安裝依賴包
    ```bash
    conda create --name FinBuddy python=3.12
    conda activate FinBuddy
    pip install -r requirements.txt
    ```

#### 啟動(第二個命令列)
* 通過Python
    ```bash
    conda activate FinBuddy
    python server.py
    ```

## 啟動N8N(第三個命令列)

* 透過docker引擎安裝並啟動n8n服務
    ```
    docker build -t custom-n8n .
    docker run -it --rm --name n8n -p 5678:5678 -v ${PWD}/data:/home/node/.n8n custom-n8n
    ```
    * `${PWD}` 是Windows底下的一個環境變數，表示當前工作目錄的絕對路徑
