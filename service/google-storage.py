from flask import Flask, Response, request, abort, send_file, stream_with_context
import datetime
import json
import os
import logging
import google.auth
from google.cloud import storage
from openssl_signer import OpenSSLSigner

app = Flask(__name__)

if os.environ.get("PROFILE"):
    from werkzeug.contrib.profiler import ProfilerMiddleware

    app.config['PROFILE'] = True
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[50])

__version__ = '0.0.2'

# Get env.vars
credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CONTENT")

# Set up logging
log_level = logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO"))
logging.basicConfig(level=log_level)  # dump log to stdout

# write out service config from env var to known file
with open(credentials_path, "wb") as out_file:
    out_file.write(credentials.encode())


@app.route("/datasets/<bucket_name>/entities", methods=["GET"])
def get_entities(bucket_name):
    logging.info("Serving request for bucket %s" % bucket_name)
    """
    Endpoint to read entities from gcp bucket, add signed url and return
    Available query parameters (all optional)
        expire: date time in format %Y-%m-%d %H:%M:%S - overrides default expire time
        with_subfolders: False by default if assigned will include blobs from subfolders
        with_prefix: optional, to filter blobs
    :return:
    """

    set_expire = request.args.get('expire')
    with_subfolders = request.args.get('with_subfolders')
    with_prefix = request.args.get('with_prefix')

    def generate():
        """Lists all the blobs in the bucket."""
        count = 0

        credentials_obj, _ = google.auth.default()
        new_signer = OpenSSLSigner.from_service_account_file(credentials_path)
        credentials_obj._signer = new_signer

        if not set_expire:
            expiration = datetime.datetime(2183, 9, 8, 13, 15)
        else:
            expiration = datetime.datetime.strptime(set_expire, '%Y-%m-%d %H:%M:%S')

        iterator = bucket.list_blobs(prefix=with_prefix,
                                     max_results=int(os.environ.get("LIMIT")) if os.environ.get(
                                         "LIMIT") else None,
                                     fields="nextPageToken,items(name,generation,updated)")
        first = True
        yield "["

        for blob in iterator:
            entity = {"_id": blob.name}
            if '/' in entity["_id"] and not with_subfolders:  # take only root folder
                continue

            if entity["_id"].endswith("/"):  # subfolder object
                continue

            entity["file_id"] = entity["_id"]

            entity["file_url"] = blob.generate_signed_url(expiration, method="GET")
            entity["updated"] = str(blob.updated)
            entity["generation"] = blob.generation

            if not first:
                yield ","
            yield json.dumps(entity)
            count += 1
            first = False
        yield "]"
        logging.info("%d elements processed", count)

    try:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        response = Response(generate(), mimetype="application/json")
        return response
    except Exception as e:
        logging.error(str(e))
        abort(e.code, e.message)


@app.route("/download/<bucket>/<path:filename>", methods=['GET'])
def download(bucket, filename):
    """
    Downloads file with given name from given bucket
    :param bucket: Google cloud storage bucket name
    :param filename: path to file (simply file name for files in root folder)
    :return: file
    """
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket)
    try:
        chunk_size = 262144 * 4 * 10
        blob = bucket.blob(filename, chunk_size=chunk_size)

        def generate():
            file_data = blob.download_as_string(start=0, end=chunk_size)
            yield file_data
            counter = chunk_size + 1  # both start and end are inclusive
            while len(file_data) >= chunk_size:
                file_data = blob.download_as_string(start=counter, end=counter + chunk_size - 1)
                yield file_data
                counter += chunk_size

        return Response(generate(), headers={'Content-Type': blob.content_type})
    except Exception as e:
        logging.error(str(e))
        abort(e.code, e.message)


@app.route("/upload/<bucket_name>", methods=["POST"])
def upload(bucket_name):
    """
    Upload file to given bucket
    :param bucket_name:
    :return: 200 code if everything OK
    """
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    files = request.files

    local_path = request.headers.get('local_path')

    for file in files:
        if files[file].filename == '':
            continue
        filename = files[file].filename

        logging.info("uploading {} to {}".format(filename, local_path))
        if local_path:
            filename = "{}/{}".format(local_path, filename)
        blob = bucket.blob(filename)
        blob.upload_from_file(files[file])
    return Response()


if __name__ == "__main__":
    # Set up logging
    format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logger = logging.getLogger("google-storage-microservice")

    # Log to stdout
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(stdout_handler)

    logger.setLevel(logging.DEBUG)
    logging.info("Starting service v.{}".format(__version__))

    app.run(threaded=True, debug=True if os.environ.get("PROFILE") else False, host='0.0.0.0',
            port=os.environ.get('PORT', 5000))
