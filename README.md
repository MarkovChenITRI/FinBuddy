# FinBuddy

![](https://github.com/MarkovChenITRI/FinBuddy/blob/main/assets/images/FinBuddy_Framework.png)


* 取得`browser-use`模組
    ```
    git submodule update --init --recursive
    ```

* 透過docker引擎安裝並啟動browse-use服務
    ```
    cd browser-use && copy .env.example .env
    docker compose up --build
    ```
    
* 透過docker引擎安裝n8n服務
    ```
    #docker run -it --rm --name n8n -p 5678:5678 -v ${PWD}/data:/home/node/.n8n docker.n8n.io/n8nio/n8n

    docker build -t custom-n8n .
    docker run -it --rm --name n8n -p 5678:5678 -v ${PWD}/data:/home/node/.n8n custom-n8n
    ```
    * `${PWD}` 是Windows底下的一個環境變數，表示當前工作目錄的絕對路徑
