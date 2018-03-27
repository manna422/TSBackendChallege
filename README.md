# Texada Software Backend Challenge

## Project requirement and description:

Create a back end with Flask or Django frameworks to complete the tasks below via API.

1.    Import the initial data set into your own SQL Database

2.    Create an API backend to add, update, or delete the records and the values within the records to track the location of a product (its Longitude, Latitude, Elevation) at a specific Date/time.

3.  Enforce data validation to ensure information integrity.

4.  Implement pagination

Bonus points for creative additional features or functionality.

# Stack

For my solution, the stack consists of:
* Flask
* SQLite
* SQLAlchemy

## Installation
Prerequisites:
* Python3
* virtualenv
* pip

The following bash command(s) are used for setting up the project:
```bash
cd <repo root directory>
make clean # optional, if first install
make install
make run # runs server
```

In a second terminal
```bash
cd <repo root directory>
./load_test_data.sh # inits DB and CURLS initial values
```

# Design Decisions
* Two tables are used for representing the data. To avoid repeatedly fetching aircraft description.

```
* denotes primary (compound) key

+-------------+     +------------------+
|  AIRCRAFT   |     | LOCATIONRECORD   |   
+-------------+     +------------------+
| * ID        |<--->| * Aircraft ID    |   
| DESCRIPTION |     | * Datetime       |   
+-------------+     | Longitude        |   
                    | Latitude         |   
                    | Elevation        |   
                    +------------------+
```
* JSON messages are used for sending data. To make parsing messages and routes more reusable.
* SQLAlchemy used as driver for DB.
  1. SQLAlchemy gives Django like ORM.
  2. SQLAlchemy allows for easy swapping between SQL DB.
* SQLite used for ease of deployment, and quick debugging. Driver allows for easy swapping to PostgreSQL.
* Primary key for LocationRecord table is a compound key of Aircraft ID and Timestamp. It seems like a logical decision to have a one entry per time per aircraft. Some of the data provided contains multiple entries that share the same time and craft ID. By design, the `POST` method will drop add conflicts like this, but the `PATCH` method will override existing entries. 
* For "Bonus points for creative additional features or functionality." The following bit started as a novel idea, but I ended up really liking the design of the dynamic filter/sort:

```Python
@app.route('/location', methods=['GET'])
def location_get():

  # ...

  # supported arguments for sorting and filtering
  suported_keys = ['id', 'datetime', 'longitude', 'latitude', 'elevation']
  supported_comparitors = {
      'eq': lambda x,y: x==y,
      'ne': lambda x,y: x!=y,
      'gt': lambda x,y: x>y,
      'ge': lambda x,y: x>=y,
      'lt': lambda x,y: x<y,
      'le': lambda x,y: x<=y,
  }   
  supported_sort_directions = ['asc', 'desc']

  filter_args = []
  sort_args = []

  for criteria in query_filters:
      if len(criteria) != 3:
          return jsonify({'error':'invalid filter args'}), 400

      key, comparitor, value = criteria
      if (key not in suported_keys) or (comparitor not in supported_comparitors):
          return jsonify({'error':'invalid filter args'}), 400

      filter_args.append(supported_comparitors[comparitor](
          LocationRecord.__dict__[key],
          value
      ))  


  # compounding list of filters using the reduce operator
  filtered_query = reduce(lambda x,y: x.filter(y), filter_args, LocationRecord.query)


  for criteria in sort_criterion:
      if len(criteria) != 2:
          return jsonify({'error':'invalid sorting args'}), 400

      key, direction = criteria
      if (key not in suported_keys) or (direction not in supported_sort_directions):
          return jsonify({'error':'invalid sorting args'}), 400

      sort_args.append('{!s} {!s}'.format(key, direction))


  # sorting data using reduce to concatenate requirements
  sorted_filtered_query = reduce(lambda x,y: x.order_by(y), sort_args, filtered_query)



  # ...
```

## TODO for more longterm production service:
* Implement Test Cases, using a combination of `pytest` testing framework and the `requests` library, or similar.
* Add support for multiple configurations: Development vs Deployment
* Authentication with flask plugin
* Include Dockerfile
* Handle each incoming JSON KEY, eg: parse timestamps for validity with regex


# API

All request to the server use JSON encoded messages instead of URL encoded params to allow for ease of code reuse

## Route - `/aircraft`
### `GET`
For looking up description for a given aircraft ID. If no ID key is provided will return a dictionary of all aircraft IDs and descriptions.

message content
```JSON
{"id":1}
```

expected output
```JSON
{
  "aircrafts": {
    "1": "Cesna 120"
  }
}
```

CURL example
```bash
curl -i -H "Content-Type: application/json" -X GET -d '{"id":1}' ${HOST_ADDRESS}/aircraft
```


### `POST`
For inserting aircraft ID and description into DB. Will not override description for an existing ID.

message content
```JSON
{"id":1, "description":"Cesna 120"}
```

expected output
```JSON
{
  "action": "POST",
  "data": {
    "description": "Cesna 120",
    "id": 1
  },
  "status": "success"
}
```

CURL example
```bash
curl -i -H "Content-Type: application/json" -X POST -d '{"id":1, "description":"Cesna 120"}' ${HOST_ADDRESS}/aircraft
```

### `PATCH`
Same as `POST` but will override previous values

CURL example
```bash
curl -i -H "Content-Type: application/json" -X PATCH -d '{"id":1, "description":"Cesna 120"}' ${HOST_ADDRESS}/aircraft
```


### `DELETE`
For deleting the description for a given aircraft ID.
input content
```JSON
{"id":1}
```

expected output
```JSON
{
  "action": "DELETE",
  "data": {
    "id": 1
  },
  "status": "success"
}
```

CURL example
```bash
curl -i -H "Content-Type: application/json" -X DELETE -d '{"id":1}' ${HOST_ADDRESS}/aircraft
```


## Route - `/location`
### `GET`
For querying location record data from the DB. Allow for multiple filters and sort keys to be provided in a single request. Pagination supported.

Query Keys

| Key | Description | Type | Example | Default | Required |
| --- | ----------- | ---- | ------- | ------- | -------- |
| page_number | get results for this page number | int | 2 | 1 | False|
|page_limit| number of records per page| int | 10 | 25 | False |
|filters|Array of search filters on each of the record keys. Each entry consists of [key, comparitor, value]. Supported comparitors are: `eq`, `ne`, `ge`, `le`, `lt`, `gt` |Array of Arrays|[["id","eq","1"], ["elevation", "ge", 500]]|[]|False|
|sort| Used for sorting results, each entry consists of a key to sort on and a directon (`asc`/`desc`)  |Array of Arrays|[["elevation","asc"], ["datetime", "desc"]]|[]|False|


message content
```json
{
  "page_number":1,
  "page_limit":2,
  "filters":[["id","eq","1"]],
  "sort":[["elevation","asc"], ["datetime", "desc"]]
}
```
expected output
```json
{
  "action": "GET",
  "page_current": 1,
  "page_total": 2,
  "query": {
    "filters": [
      [
        "id",
        "eq",
        "1"
      ],
      [
        "elevation",
        "ge",
        500
      ]
    ],
    "page_limit": 2,
    "page_number": 1,
    "sort": [
      [
        "elevation",
        "asc"
      ],
      [
        "datetime",
        "desc"
      ]
    ]
  },
  "results": [
    {
      "datetime": "2016-10-12T12:00:00",
      "elevation": 500,
      "id": 1,
      "latitude": -81.8149807,
      "longitude": 43.2583264
    },
    {
      "datetime": "2016-10-13T12:00:00",
      "elevation": 550,
      "id": 1,
      "latitude": -79.286693,
      "longitude": 42.559112
    }
  ],
  "status": "success"
}
```
CURL example
```bash
curl -i -H "Content-Type: application/json" -X GET -d '{"page_number":1, "page_limit":2, "filters":[["id","eq","1"], ["elevation", "ge", 500]],"sort":[["elevation","asc"], ["datetime", "desc"]]}' ${HOST_ADDRESS}/location
```

### `POST`
For inserting location records into the database. **All** keys are required.
message content. Will not allow previous entries of matching (ID, datetime) to be overridden.

```json
{
  "id":1,
  "datetime":"2016-10-12T12:00:00-05:00", # iso-formatted time
  "longitude":43.2583264,
  "latitude":-81.8149807,
  "elevation":500
}
```
expected output
```json
{
  "action": "POST",
  "data": {
    "datetime": "2016-10-12T12:00:00-05:00",
    "elevation": 500,
    "id": 1,
    "latitude": -81.8149807,
    "longitude": 43.2583264
  },
  "status": "success"
}
```
CURL example
```bash
curl -i -H "Content-Type: application/json" -X POST -d '{"id":1, "datetime":"2016-10-12T12:00:00-05:00", "longitude":43.2583264, "latitude":-81.8149807, "elevation":500}' ${HOST_ADDRESS}/location
```

### `PATCH`
Same as `POST` but will allow for overriding.


### `DELETE`
Requires Aircraft ID and Timestamp. Will delete record entries matching those keys
message content
```json
{
  "id":1,
  "datetime": "2016-10-14T12:00:00"
}
```
expected output
```json
{
  "action": "DELETE",
  "data": {
    "datetime": "2016-10-14T12:00:00",
    "id": 1
  },
  "status": "success"
}
```
CURL example
```bash
curl -i -H "Content-Type: application/json" -X DELETE -d '{"id":1, "datetime": "2016-10-14T12:00:00"}' ${HOST_ADDRESS}/location
```
