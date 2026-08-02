FROM python:3.9-slim
# Set working directory
WORKDIR /app

# Install libraries
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install  -r requirements.txt



# Copy package code
COPY app app

CMD [ "python", "app/main.py" ]