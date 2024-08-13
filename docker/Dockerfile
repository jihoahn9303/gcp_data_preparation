FROM python:3.10-slim

ARG USER_ID
ARG USER_NAME

ENV HOME=/home/${USER_NAME} \
    VIRTUAL_ENV=/home/${USER_NAME}/venv 
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Seoul \
    PATH="/usr/local/gcloud/google-cloud-sdk/bin:${VIRTUAL_ENV}/bin:${HOME}/.local/bin:${PATH}" \
    PYTHONPATH="/app:${PYTHONPATH}" \
    BUILD_POETRY_LOCK="${HOME}/poetry.lock.build"

RUN apt-get update \
    && apt-get -qq -y install vim gcc curl git build-essential libb64-dev software-properties-common \
    && curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-462.0.1-linux-x86_64.tar.gz \
    && mkdir -p /usr/local/gcloud \
    && tar -C /usr/local/gcloud -zxvf google-cloud-cli-462.0.1-linux-x86_64.tar.gz \
    && /usr/local/gcloud/google-cloud-sdk/install.sh --usage-reporting false --command-completion true --bash-completion true --path-update true --quiet \
    && rm google-cloud-cli-462.0.1-linux-x86_64.tar.gz \
    && apt-get -qq -y clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir -p ${HOME} /app 
COPY . /app/

RUN chmod a+x /app/docker/scripts/*.sh \
    && addgroup --system --gid ${USER_ID} ${USER_NAME} \
    && useradd --system --no-log-init \
    --home-dir ${HOME} \
    --uid ${USER_ID} \
    --gid ${USER_NAME} \
    --groups ${USER_NAME} ${USER_NAME} \
    && chown -R ${USER_NAME}:${USER_NAME} /app /tmp ${HOME}

USER ${USER_NAME}:${USER_NAME}
RUN curl -sSL https://install.python-poetry.org | python3 -
    
WORKDIR /app
RUN poetry config virtualenvs.create false \
    && python3.10 -m venv ${VIRTUAL_ENV} \
    && pip install --upgrade pip setuptools \
    && poetry install \
    && cp poetry.lock ${BUILD_POETRY_LOCK} \
    && rm -rf ${HOME}/.cache/* \
    && python3.10 -m nltk.downloader stopwords && python3.10 -m nltk.downloader punkt \
    && git config --global user.email "rediate03@gmail.com" \
    && git config --global user.name "jihoahn9303"

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["/app/docker/scripts/startup-script.sh"]



