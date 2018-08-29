from flask import Flask, Response, request
import datetime
import json
import os
import logging
from google.cloud import storage
import requests

app = Flask(__name__)


credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CONTENT")

# write out service config from env var to known file
with open(credentials_path, "wb") as out_file:
    out_file.write(credentials.encode())


storage_client = storage.Client()

buckets = storage_client.list_buckets()

print('Buckets:')
for bucket in buckets:
    print(bucket)

# get blobs in outgoing
blobs = bucket.list_blobs(prefix='incoming/', delimiter='/')
# blobs = bucket.list_blobs()

print('Blobs:')
for blob in blobs:
    print(blob.name)
    expiration = datetime.datetime(2055, 7, 14, 12, 30)
    encurl = blob.generate_signed_url(expiration, method='GET')
    print(encurl)

print("done")


@app.route('/config', methods=["GET", "POST"])
def get_files():

    # google store target location
    remote_file_path = 'incoming/'

    # catch the posted data
    source_file_config = request.get_json()

    logger.debug('source file config: {}'.format(source_file_config))

    for entity in source_file_config:
        # get file config for hosted files
        source_file_name = entity['file_id']
        source_file_path = entity['file_url']

        logger.debug('source file: {}{}'.format(source_file_path, source_file_name))

        # download hosted files locally
        r = requests.get(source_file_path + source_file_name, stream=True)

        tmp_file = 'tmp'
        with open(tmp_file, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

        # upload local files to google store
        blob = bucket.blob(remote_file_path + source_file_name)
        blob.upload_from_filename(tmp_file)

        # clean up local files
        os.remove(tmp_file)

        logger.info('File {} uploaded to {}.'.format(source_file_path + source_file_name, blob))

    return Response(json.dumps(source_file_config), mimetype='text/plain')


if __name__ == '__main__':
    # Set up logging
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger('google-storage-microservice')

    # Log to stdout
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(stdout_handler)

    logger.setLevel(logging.DEBUG)

    app.run(threaded=True, debug=True, host='0.0.0.0')