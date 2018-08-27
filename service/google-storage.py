from flask import Flask, Response, request
import datetime
import json
import os
import logging
from google.cloud import storage

app = Flask(__name__)

google_store_credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CONTENT")

# write out service config from env var to known file

# f = open(google_store_credentials_path, "wb") # Why the heck is this not writing valid json?!?
# f.write(credentials.encode())

with open(google_store_credentials_path, "wb") as out_file:
    out_file.write(credentials.encode())


storage_client = storage.Client()

buckets = storage_client.list_buckets()

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


@app.route('/files/{value}', methods=['GET'])
def get_file():
   pass


# Read from metadata file for manually uploaded files
@app.route('/entities', methods=['GET'])
def get_entities():
    def generate():
        objs = []
        first = True
        yield "["
        for key in objs:
            # do something with the key
            entity = {"_id": key }
            if not first:
                yield ","
            yield json.dumps(entity)
            first = False
        yield "]"

    return Response(generate(), mimetype='application/json')


@app.route('/entities', methods=['POST'])
def post_entities():
    entities = request.get_json()
    for entity in entities:
        entity_id = entity["_id"]
        fileUrl = entity["fileUrl"]

        # get file and upload to google

    return Response("Thanks!", mimetype='text/plain')


if __name__ == '__main__':
    # Set up logging
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger('redis')

    # Log to stdout
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(stdout_handler)

    logger.setLevel(logging.DEBUG)

    app.run(threaded=True, debug=True, host='0.0.0.0')