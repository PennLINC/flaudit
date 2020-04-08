From rocker/verse:3.3.1

# GET PYTHON >= 3.7
# https://forums.docker.com/t/how-can-i-install-python-3-6-version-on-top-of-r/68867/3
ARG BUILDDIR="/tmp/build"
ARG PYTHON_VER="3.7"
WORKDIR ${BUILDDIR}

RUN apt-get update -qq && \
apt-get upgrade -y  > /dev/null 2>&1 && \
apt-get install wget gcc make zlib1g-dev -y -qq > /dev/null 2>&1 && \
wget --quiet https://www.python.org/ftp/python/${PYTHON_VER}/Python-${PYTHON_VER}.tgz > /dev/null 2>&1 && \
tar zxf Python-${PYTHON_VER}.tgz && \
cd Python-${PYTHON_VER} && \
./configure  > /dev/null 2>&1 && \
make > /dev/null 2>&1 && \
make install > /dev/null 2>&1 && \
rm -rf ${BUILDDIR} 

# GET PIP
RUN apt-get install -y python3-pip
#RUN cp /usr/bin/python3 /usr/bin/python

MAINTAINER Tinashe Tapera <taperat@pennmedicine.upenn.edu>

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json ${FLYWHEEL}/manifest.json

# install necessary packages for python
RUN python3 -m pip install --upgrade pip
RUN pip install --no-cache nipype
RUN pip install --no-cache pandas
RUN pip install --no-cache tqdm
RUN pip install --no-cache flywheel-sdk==11.*
RUN pip install --no-cache fw-heudiconv

# install necessary packages for R

RUN Rscript -e "install.packages(c('rmarkdown', 'tidyverse', 'knitr', 'scales', 'ggrepel', 'wordcloud', 'DT', 'naniar', 'gdata', 'lubridate', 'collapsibleTree', 'ggalluvial', 'networkD3'), repos = 'http://cran.us.r-project.org')"

# Copy necessary files

COPY . ${FLYWHEEL}

# Set the entrypoint
ENTRYPOINT ["run_audit.py"]