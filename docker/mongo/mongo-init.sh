#!/bin/bash
mongo -- "$MONGO_INITDB_DATABASE" <<EOF

  var user = '$MONGO_INITDB_USERNAME';
  var passwd = '$MONGO_INITDB_PASSWORD';
  var database = '$MONGO_INITDB_DATABASE'

  db.createUser({
    user: user,
    pwd: passwd,
    roles: [
      {
        role: "readWrite",
        db: database
      }
    ]
  });
EOF
