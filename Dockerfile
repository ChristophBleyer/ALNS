FROM python:3

COPY . /App

WORKDIR /App

RUN pip install --no-cache-dir -r requirements.txt

CMD ["jupyter", "notebook", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root"]