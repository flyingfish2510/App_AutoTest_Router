FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

CMD ["pytest", "-v", "--tb=short"]