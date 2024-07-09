# tracker

- request uid
- request text
- response text

Notification of messages coming in. Timestamp
Notification of message going out. Timestamp

message tracker
byte(16)          : uid
request           : str
request_timestamp : timestamp 
response          : str
response_timestamp: timestamp

- A notification, indicating that a request has come into the system
  - a record is created in the database with the
    - the request uid
    - request string
    - timestamp
- A notification, indicating that a response is leaving the system
  - The record with the request uid is updated with
    - the response string
    - the response timestamp
