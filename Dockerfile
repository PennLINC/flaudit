FROM rocker/verse:3.3.1

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY manifest.json ${FLYWHEEL}/manifest.json
MAINTAINER Tinashe Tapera <taperat@pennmedicine.upenn.edu>

# WE EXPORT PATH FOR CONDA
ENV PATH="/opt/conda/bin:${PATH}"

# UPDATE A SERIES OF PACKAGES
RUN apt-get update --fix-missing && apt-get install -y ca-certificates libglib2.0-0 libxext6 libsm6 libxrender1 libxml2-dev


# INSTALL PYTHON 3 AND ANACONDA
RUN apt-get install -y python3-pip python3-dev && pip3 install virtualenv \
&& wget --quiet https://repo.anaconda.com/archive/Anaconda3-5.3.0-Linux-x86_64.sh -O ~/anaconda.sh \
&& /bin/bash ~/anaconda.sh -b -p /opt/conda && rm ~/anaconda.sh \
&& ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh \
&& echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc

# ACTIVATE CONDA ENVIRONMENT
RUN echo "source activate base" > ~/.bashrc

# install necessary packages for python
RUN pip install --no-cache nipype
RUN pip install --no-cache pandas
RUN pip install --no-cache tqdm
RUN pip install --no-cache flywheel-sdk==11.*
RUN pip install --no-cache fw-heudiconv

# install necessary packages for R

RUN Rscript -e "install.packages(c('dplyr', 'stringr', 'tidyr', 'ggplot2', 'purrr', 'rmarkdown', 'knitr', 'scales', 'ggrepel', 'wordcloud', 'naniar', 'gdata', 'lubridate', 'collapsibleTree', 'ggalluvial', 'networkD3', 'data.table'), repos = 'http://cran.us.r-project.org')"

# Copy necessary files

COPY . ${FLYWHEEL}

# Set the entrypoint
ENTRYPOINT ["/flywheel/v0/run_audit.py"]
WORKDIR /flywheel/v0
