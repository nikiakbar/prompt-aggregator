FROM public.ecr.aws/docker/library/python:3.12-slim

# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy source code
COPY . .

# Expose port 4000
EXPOSE 4000

# Run the app
CMD ["python", "app.py"]
