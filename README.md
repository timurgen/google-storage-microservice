# google-storage-microservice

## Environment variables

`GOOGLE_APPLICATION_CREDENTIALS` - Path to Google Storage credential file. 

`GOOGLE_APPLICATION_CREDENTIALS_CONTENT` - Content of Google Storage credential file. This content is written to the file specified in `GOOGLE_APPLICATION_CREDENTIALS`. 

## Usage

The microservice listens to `/config` at port 5000 and expects JSON formatted config for where it is to fetch source files:

```
[
    {
        "file_id": "some-file-name",
        "file_url": "url/to/file/"
    },
    ...
]
```

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