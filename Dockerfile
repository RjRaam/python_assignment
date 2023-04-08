FROM python:3.8.5

WORKDIR /python_assignment

COPY ./requirements.txt /python_assignment/requirements.txt

RUN pip install -r requirements.txt

COPY . /python_assignment

#RUN apk --update-cache add sqlite \
#    && rm -rf /var/cache/apk/* \
#    && ./financial/create-db.sh \
#    && chmod a+rw ./financial/assignment.db
##    && chmod a+rw ./financial/assignment.sqlite \

ENTRYPOINT [ "python" ]
CMD [ "./financial/app.py" ]