# Getting Started & FAQ

## Quick Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd permit-fastmcp
   ```
2. **Set up a virtual environment**
   ```bash
   uv venv
   source .venv/bin/activate
   uv sync
   ```
3. **Run the example server**
   ```bash
   python permit_fastmcp/example_server/example.py
   ```
4. **Login to get a JWT token**
   Use the `login` tool with username/password (e.g., `admin`/`password` or `client`/`client`). This will return a JWT token.
   #### Note 
    The `login` tool in this example is NOT the standard way to obtain a JWT in production. It is included only for simplicity and to make demoing/experimenting with the example server easy. In real-world scenarios, JWTs should be issued by your authentication provider (e.g., Auth0, Okta, your own IdP).

5. **Call a tool with JWT authentication**
   Use the `greet-jwt` tool, passing the JWT as a Bearer token in the `Authorization` header:
   ```http
   Authorization: Bearer <your-token>
   ```

## FAQ

**Q: Why am I getting 'Unauthorized' errors?**
- Make sure your user is assigned the correct role in the Permit.io Directory.
- Check your policy mapping and resource/action names.
- Ensure your JWT or header is set correctly.

**Q: How do I add new tools or resources?**
- Define new tools with `@mcp.tool` in your FastMCP server.
- Update your Permit.io policies to grant access to the new actions/resources.

**Q: How do I debug authorization issues?**
- Enable debug logging in your server:
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  ```
- Check the server logs for detailed authorization events.

For more, see the main README and the other docs in this folder. 