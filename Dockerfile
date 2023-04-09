FROM python:3.8.5

WORKDIR /python_assignment

COPY ./requirements.txt /python_assignment/requirements.txt

RUN pip install -r requirements.txt

COPY . /python_assignment

EXPOSE 4321

ENV FLASK_APP="./financial/app.py"

CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4321"]