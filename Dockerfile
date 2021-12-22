FROM public.ecr.aws/lambda/python:3.8

# Copy function code
COPY app.py ${LAMBDA_TASK_ROOT}
COPY requirements.txt .
COPY Take_Action.mp3 .
ENV NUMBA_CACHE_DIR=/tmp/
ENV AWS_ACCESS_KEY_ID=
ENV AWS_SECRET_ACCESS_KEY=
ENV AWS_DEFAULT_REGION=
ENV AWS_S3_BUCKET=
# Install the function's dependencies using file requirements.txt
# from your project folder.
RUN yum -y update && \
  yum -y install wget xz bzip2 bzip2-devel openssl openssl-devel readline readline-devel sqlite-devel && \
  yum -y install cmake libjpeg-devel libtiff-devel libpng-devel jasper-devel && \
  yum -y install mesa-libGL-devel libXt-devel libgphoto2-devel nasm libtheora-devel libsndfile && \
  yum -y install autoconf automake libtool yasm openal-devel blas blas-devel atlas atlas-devel lapack lapack-devel

RUN python3 -m pip install --upgrade pip && \
  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# RUN cd /usr/local/bin && mkdir ffmpeg && cd ffmpeg && \
#   wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
#   tar -xf ffmpeg-release-amd64-static.tar.xz && \
#   chmod 755 /usr/local/bin/ffmpeg/ffmpeg-4.4.1-amd64-static/ffmpeg && \
#   cp /usr/local/bin/ffmpeg/ffmpeg-4.4.1-amd64-static/ffmpeg /tmp/ffmpeg && \
#   ln -s /usr/local/bin/ffmpeg/ffmpeg-4.4.1-amd64-static/ffmpeg /usr/bin/ffmpeg && \
#   chmod 755 /tmp/ffmpeg && echo 'export PATH=$PATH:/tmp' > ~/.bashrc && source ~/.bashrc

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "app.handler" ] 
