FROM ubuntu:latest

ARG DEBIAN_FRONTEND=noninteractive

## Install Packages/Libraries ##
RUN apt-get update -y && \
    apt-get install -y \
        python3-pip \
        python3-dev \
        gfortran \
        libopenblas-dev \
        liblapack-dev \
        wget \
        unzip \
        vim \
        curl \
        sudo \
        nmap \
        iproute2 \
        iptables \
        net-tools \
        nodejs

COPY ./requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Create workking directory.
RUN mkdir /app
WORKDIR   /app
