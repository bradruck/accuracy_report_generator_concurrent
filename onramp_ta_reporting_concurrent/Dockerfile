# Use Python 3 image as our launching point
FROM python:3.6-onbuild

# Maintainer of App
MAINTAINER bradley.ruck@oracle.com

# Copy files from the host into the container
ADD . .

# Set the UID (or username)
USER 616585791:616585791

# Additional commands/dependencies to execute
RUN pip install --no-cache-dir -r requirements.txt

#WORKDIR onramp_ta_reporting_concurrent

CMD [ "python", "main.py" ]
