#GET ALL REQ PACKAGE
FROM python:3.13-slim
#STORE IN /app
WORKDIR /app
#COPY THE REQUIREMENTS IN /app/ 
COPY requirements.txt /app/requirements.txt
#ONLY INSTALL REQUIREMENTS
RUN pip install -r requirements.txt
#COPY EVERYTHING IN CONTAINER
COPY . .
#APPLICATION RUNS ON 8501 PORT
EXPOSE 8501
#EXECUTION
CMD [ "streamlit", "run", "app.py" ]