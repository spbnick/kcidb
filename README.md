KCIDB
=====

Kcidb is a package for entering and querying data to/from the Linux Kernel CI
common report database.

Setup
-----

To install the package for the current user, run this command:

    pip3 install --user <SOURCE>

Where `<SOURCE>` is the location of the package source, e.g. a git repo:

    pip3 install --user git+https://github.com/spbnick/kcidb.git

or a directory path:

    pip3 install --user .

If you want to hack on the source code, install the package in the editable
mode with the `-e/--editable` option, and with "dev" extra included. E.g.:

    pip3 install --user --editable '.[dev]'

The latter installs kcidb executables which use the modules from the source
directory, and changes to them will be reflected immediately without the need
to reinstall. It also installs extra development tools, such as `flake8` and
`pylint`.

In any case, make sure your PATH includes the `~/.local/bin` directory, e.g.
with:

    export PATH="$PATH":~/.local/bin

BigQuery
--------

Kcidb uses Google BigQuery for data storage. To be able to store or query
anything you need to create a BigQuery dataset.

The documentation to set up a BigQuery account with a data set and a token can
be found here:
https://cloud.google.com/bigquery/docs/quickstarts/quickstart-client-libraries

Alternatively, you may follow these quick steps:

1. Create a Google account if you don't already have one
2. Go to the "Google Cloud Console" for BigQuery: https://console.cloud.google.com/projectselector2/bigquery
3. "CREATE" a new project, enter arbitrary project name e.g. `kernelci001`
4. "CREATE DATASET" in that new project with an arbitrary ID e.g. `kernelci001a`
5. Go to "Google Cloud Platform" -> "APIs & Services" -> "Credentials",
   or this URL if you called your project `kernelci001`: https://console.cloud.google.com/apis/credentials?project=kernelci001
6. Go to "Create credentials" and select "Service Account Key"
7. Fill these values:
  * Service Account Name: arbitrary e.g. `admin`
  * Role: Owner
  * Format: JSON
8. "Create" to automatically download the JSON file with your credentials.


Usage
-----
Before you execute any of the tools make sure you have the path to your
BigQuery credentials stored in the `GOOGLE_APPLICATION_CREDENTIALS` variable.
E.g.:

    export GOOGLE_APPLICATION_CREDENTIALS=~/.bq.json

To initialize the dataset, execute `kcidb-init -d <DATASET>`, where
`<DATASET>` is the name of the dataset to initialize.

To submit records use `kcidb-submit`, to query records - `kcidb-query`.
Both use the same JSON schema on standard input and output respectively, which
can be displayed by `kcidb-schema`.

To cleanup the dataset (remove the tables) use `kcidb-cleanup`.

Upgrading
---------

To upgrade the dataset schema, do the following.

1. Authenticate to Google Cloud with the key file (`~/.kernelci-bq.json`
   here):

        gcloud auth activate-service-account --key-file ~/.kernelci-bq.json

   or login with your credentials (entered via a browser window):

        gcloud auth login

2. Create a new dataset (`kernelci02` in project `kernelci` here) with the new
   schema:

        bq mk --project_id=kernelci kernelci02
        # Using new-schema kcidb
        kcidb-init -d kernelci02

3. Switch all data submitters to using new-schema kcidb and the newly-created
   dataset.

4. Disable write access to the old dataset using BigQuery management console.

5. Transfer data from the old dataset (named `kernelci01` here) to the new
   dataset (named `kernelci02` here) using old-schema `kcidb-query` and
   new-schema `kcidb-submit`.

        # Using old-schema kcidb
        kcidb-query -d kernelci01 > kernelci01.json
        # Using new-schema kcidb
        kcidb-submit -d kernelci02 < kernelci01.json

API
---
You can use the `kcidb` module to do everything the command-line tools do.

First, make sure you have the `GOOGLE_APPLICATION_CREDENTIALS` environment
variable set and pointing at the Google Cloud credentials file. Then you can
create the client with `kcidb.Client(<dataset_name>)` and call its `init()`,
`cleanup()`, `submit()` and `query()` methods.

You can find the I/O schema `in kcidb.io_schema.JSON` and use
`kcidb.io_schema.validate()` to validate your I/O data.

See the source code for additional documentation.
