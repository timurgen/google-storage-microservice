# google-storage-microservice

## Environment variables

`GOOGLE_APPLICATION_CREDENTIALS` - Path to Google Storage credential file (json format file for service account authentication). 

`GOOGLE_APPLICATION_CREDENTIALS_CONTENT` - Content of Google Storage credential file. This content is written to the file specified in `GOOGLE_APPLICATION_CREDENTIALS`. 

## Usage

The microservice listens to the following endpoints at port 5000:

`/upload` - JSON formatted config for where it is to fetch source files for upload to google storage

`/entities` - returns JSON formatted entities listing all files at the google storage  
Available query parameters (all optional)  
* expire: date time in format %Y-%m-%d %H:%M:%S - overrides default expire time
* with_subfolders: False by default if assigned will include blobs from subfolders
```
[
    {
        "file_id": "some-file-name",
        "file_url": "url/to/file/" <- signed URL with expiration date
    },
    ...
]
```

`/download/<bucket name>/<file path>` - downloads file from Google Storage Bucket  
file path may include slashes to download file from bucket sub-folder


## Example System Config
```
{
  "_id": "google-storage-microservice",
  "type": "system:microservice",
  "docker": {
    "environment": {
      "GOOGLE_APPLICATION_CREDENTIALS": "google-store-credentials.json",
      "GOOGLE_APPLICATION_CREDENTIALS_CONTENT": "$SECRET(google-storage-credential-content)"
    },
    "image": "sesamcommunity/google-storage-microservice:latest",
    "port": 5000
  }
}
```