# from python 3.10

FROM python:3.10-alpine

ARG TOKEN
ARG ATLAS_URI
ARG DB_NAME

# RUN curl -sSL https://install.python-poetry.org | python3 -

# ENV PATH="${PATH}:/root/.poetry/bin"

WORKDIR .

COPY . .

# RUN poetry install

RUN pip install -r requirements.txt

ENTRYPOINT ["python src/main.py"]
