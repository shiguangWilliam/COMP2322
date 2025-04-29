# Requirements
- Python 3.x installed on your system.
- Ensure the `config.json` file is properly configured.
- Ensure the cache folder and `cache_table.json` file are in correct place.
- You can change the configs in `config.json` file to customize the server's behavior.

## Configuration
- The server configuration is stored in a JSON file named `config.json`.
- The configuration file must located in the root directory of both server and client and named as `config.json`.
- The configuration file should contain the following keys:
  - `host`: The host address to bind the server to.
  - `port`: The port number to listen on.
  - `root`: The root directory where the server will look for files.
  - `cache_folder`: The folder where the client will store cached files.
  - `cache_table_file`: The file where the client will store the cache table.
- example config is in the zip file of source code.

### Running the Server
1. Navigate to the project directory.
2. Run the server:
   ```bash
   python server.py
   ```
3. The server will start listening on the configured host and port.

### Running the Client
1. Navigate to the project directory.
2. Run the client:
   ```bash
   python client.py
   ```
3. Follow the prompts to enter commands:
   - Example command: `GET /path/to/file text keep-alive`
   - Supported methods: `GET`, `HEAD`.
   - File types: `text`, `image`.
   - Connection types(optional): `keep-alive`, `close`.

## Notes ##
- If cache table is not found, the client will not work, you have to create it by yourself.
- If cache table has exception as `json.decoder.JSONDecodeError`, you can try to add an empty `{}` to the file.
- The file send by server will be stored under the same name path under the root directory of client. For your test, you'd better set the root directory of client and server differently.
For example, you can set the root directory of client as `./client` and the root directory of server as `./server`.
- The project only support following types:
  - "txt":"text",
  - "html":"text",
  - "css":"text",
  - "js":"text",
  - "json":"text",
  - "jpg":"image",
  - "jpeg":"image",
  - "png":"image",