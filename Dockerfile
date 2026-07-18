FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE $PORT
CMD ["gunicorn", "url_shortener.wsgi", "--bind", "0.0.0.0:$PORT", "--workers", "2"]
