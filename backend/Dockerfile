FROM python:3.7-slim
WORKDIR /app
COPY requirements.txt ./
RUN apt update && \
	apt upgrade -y && \
	python3 -m pip install --upgrade pip && \
	pip install -r requirements.txt --no-cache-dir
COPY ./ ./
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]
