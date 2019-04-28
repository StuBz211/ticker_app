# A simple Flask app container.
FROM python:3.6
LABEL maintainer="Vadim Sultanov"

# Place app in container.
COPY . otp/ticker_app
WORKDIR otp/ticker_app

# Install dependencies.
RUN pip install -r requirements.txt

EXPOSE 80
CMD python app.py
