from flask import Flask, Response, request
import datetime
import json
import os
import logging
from google.cloud import storage
import requests

app = Flask(__name__)

# Get env.vars
credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CONTENT")

# Set up logging
log_level = logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO"))  # default log level = INFO
logging.basicConfig(level=log_level)  # dump log to stdout
format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logger = logging.getLogger("google-storage-microservice")

# Log to stdout
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(logging.Formatter(format_string))
logger.addHandler(stdout_handler)


# write out service config from env var to known file
with open(credentials_path, "wb") as out_file:
    out_file.write(credentials.encode())

# Instantiates a client
storage_client = storage.Client()

# Get all buckets in the project associated to the client
buckets = storage_client.list_buckets()

# print("Buckets:")
for bucket in buckets:
    logger.debug(bucket)

# get blobs in outgoing
#incoming_blobs = bucket.list_blobs(prefix='incoming/', delimiter='/')
#outgoing_blobs = bucket.list_blobs(prefix='outgoing/', delimiter='/')
#blobs = bucket.list_blobs()

# print('Blobs:')
# for blob in blobs:
#     print(blob.name)
#     expiration = datetime.datetime(2055, 7, 14, 12, 30)
#     encurl = blob.generate_signed_url(expiration, method='GET')
#     print(encurl)

print("done")


# Read from metadata file for manually uploaded files
@app.route("/entities", methods=["GET"])
def get_entities():

    def generate():

        blobs = bucket.list_blobs(prefix="outgoing/", delimiter="/")   # FIXME: parameterize

        first = True
        yield "["
        for blob in blobs:
            # do something with the key
            entity = {"_id": str.split(blob.name, "/")[-1]}  # keep file name only
            if entity["_id"] == "": continue  # skip if no file name
            expiration = datetime.datetime(2055, 7, 14, 12, 30)
            entity["file_url"] = blob.generate_signed_url(expiration, method="GET")

            if not first:
                yield ","
            yield json.dumps(entity)
            first = False
        yield "]"

    return Response(generate(), mimetype="application/json")


# download file from google storage
@app.route("/download", methods=["POST"])
def download():
    # catch the posted data
    file_config = request.get_json()

    logger.debug("source file config: {}".format(file_config))

    for entity in file_config:
        source_file_name = entity["file_id"]
        source_file_path = entity["file_url"]

        logger.debug("source file: {}{}".format(source_file_path, source_file_name))

        blob = bucket.blob(source_file_name + source_file_name)

        # FIXME
        tmp_file = "tmp"
        with open(tmp_file, "wb") as out_file:
            blob.download_to_filename(out_file)

    return Response(json.dumps(file_config), mimetype="text/plain")


# upload file to google storage
@app.route("/upload", methods=["POST"])
def upload():

    # google store target location
    remote_file_path = "incoming/"  # FIXME: parameterize

    # catch the posted data
    source_file_config = request.get_json()

    logger.debug("source file config: {}".format(source_file_config))

    for entity in source_file_config:
        # get file config for hosted files
        source_file_name = entity["file_id"]
        source_file_path = entity["file_url"]

        logger.debug("source file: {}{}".format(source_file_path, source_file_name))

        # download hosted files locally
        r = requests.get(source_file_path + source_file_name, stream=True)

        tmp_file = "tmp"
        with open(tmp_file, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

        # upload local files to google store
        blob = bucket.blob(remote_file_path + source_file_name)
        blob.upload_from_filename(tmp_file)

        # clean up local files
        os.remove(tmp_file)

        logger.info("File {} uploaded to {}.".format(source_file_path + source_file_name, blob))

    return Response(json.dumps(source_file_config), mimetype="text/plain")


if __name__ == "__main__":
    # Set up logging
    format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logger = logging.getLogger("google-storage-microservice")

    # Log to stdout
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(stdout_handler)

    logger.setLevel(logging.DEBUG)

    app.run(threaded=True, debug=True, host='0.0.0.0')