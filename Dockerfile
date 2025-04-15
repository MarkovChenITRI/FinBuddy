FROM ubuntu:22.04

COPY . /app
WORKDIR /app

RUN apt update && apt install -y bash
RUN apt install -y python3-pip
RUN bash -c "pip install -r requirements.txt"

EXPOSE 80

CMD ["python3" ,"-u" , "app.py"]
#CMD ["/bin/bash"]