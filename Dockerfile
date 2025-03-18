FROM python:3.12-slim

WORKDIR /app

# Copy requirements file separately to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Install the package
RUN pip install --no-cache-dir -e .

# Create a non-root user to run the application
RUN useradd -m appuser
USER appuser

# Set entry point to the CLI
ENTRYPOINT ["alb-rules"]
CMD ["--help"]