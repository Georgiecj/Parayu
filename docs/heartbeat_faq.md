# FAQs

## 1. Heartbeat is Not Being Written

**What is Heartbeat?**

- *Heartbeat* is the internal name given to all valid processed data from iDEC.
- It is also the name of the Elasticsearch (ES) index where processed data is written.
- **Heartbeat index format:** `<env>_<tenant_id>_heartbeat`
  - `env` stands for environment: `dev`, `uat`, or `prod`.

**How is Heartbeat data generated?**

- Heartbeat data is produced by our Spark application called **Mind-Core**.
- **Mind-Core** is developed by the data engineering team at iDEC, known as **Titans**.

---

### Reasons Why Heartbeat Data Might Not Be Written

#### 1. Mind-Core is Down

- Check the ES index `<env>_rawdata`.
  - If the `latency.processedTimestamp` field in the latest record is older than 3 days, Mind-Core may be down.
- Alternatively, confirm with the DevOps team.

#### 2. Invalid Type4 or Type2 Mapping

- If raw data sent to Mind-Core has an invalid Type4 or Type2 record:
  - Data is redirected to:
    - `<env>_<tenant_id>_unmapped`: valid tenant ID but invalid Type4/Type2 mapping.
    - `<env>__unmapped`: invalid tenant ID and invalid Type4/Type2 mapping.

#### 3. Incorrect iDEC Golden Data Format

- Mind-Core expects data in iDEC’s **Golden Data Format**.
- Invalid format leads to data being redirected to the fallback index:  
  `<env>_fallback`.

**Example of Valid iDEC Golden JSON Format:**

<details>
<summary>Click to expand</summary>

```json
{
  "system": {
    "plv": "1.3",
    "fwv": "1.0",
    "did": "mac",
    "gid": "gateway_id",
    "cid": "client_id",
    "tmstp": "2021-02-26T08:46:26+0530",
    "mtyp": 1
  },
  "attr": {
    "chr": 1,
    "batr": "99.99",
    "tmp": 1
  },
  "gnss": {
    "nmea": {
      "val": ["$GPRMC,085814.329,A,0118.072,N,10351.741,E,,,260421,000.0,W*78"]
    },
    "geometry": {
      "type": "Point",
      "coordinates": {
        "val": [[125.6, 10.1], [125.6, 10.1]]
      }
    },
    "bcn": {
      "val": [{
        "val": [{
          "bid": "SIMBD00002",
          "rssi": -77.0,
          "batr": 100
        }, {
          "bid": "SIMBD00002",
          "rssi": -77.0,
          "batr": 100
        }]
      }]
    },
    "si": 60
  },
  "data": {
    "analog_in": {
      "channel_1": {
        "val": [108.0, 78.0]
      },
      "channel_2": {
        "val": [108.0, 78.0]
      },
      "si": 60
    },
    "digital_in": {
      "channel_1": {
        "val": [108.0, 78.0]
      },
      "channel_2": {
        "val": [108.0, 78.0]
      },
      "si": 60
    }
  },
  "stats": {
    "analog_in": {
      "channel_1": {
        "val": [{
          "mean": 12.00,
          "median": 12.00,
          "variance": 2.00,
          "sd": 1.00,
          "tss": 126.00,
          "absdev": 1.00,
          "skew": 0.00,
          "kurtosis": -1.00,
          "lag_autocoorelation": 0.00,
          "largest": 15.00,
          "smallest": 10.00,
          "max_index": 14,
          "min_index": 0
        }]
      }
    }
  },
  "dtc": [
    {
      "code": "101AXV",
      "remarks": "fff"
    },
    {
      "code": "101AXV",
      "remarks": "fff"
    }
  ],
  "diagnostics": {
    "peripheral": [
      {
        "systemType": "SCANNER",
        "message": "Scanner serial port is connected",
        "errorCode": 0,
        "macId": "90:2e:16:f8:14:53",
        "isError": 0
      },
      {
        "systemType": "CAMERA",
        "message": "Scanner serial port is connected",
        "errorCode": 0,
        "macId": "90:2e:16:f8:14:53",
        "isError": 0
      }
    ]
  }
}
```

</details>

---

#### 4. Application Error

- Heartbeat data will not be written if an error occurs during processing.
- Check the `<env>_error` ES index for entries from Mind-Core.
  - Look for the `source` field in error documents; if the source is `"iDECMind"`, the error originates from Mind-Core.