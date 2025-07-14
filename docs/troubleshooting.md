# Troubleshooting

This document covers common issues and solutions for `permit-fastmcp`.

## Common Issues

### PDP Connection Error
- **Symptom:** Errors connecting to the Permit.io PDP.
- **Solution:**
  - Ensure your PDP container is running and accessible at the configured URL.
  - Check your `PERMIT_MCP_PERMIT_PDP_URL` setting.

### Authorization Denied
- **Symptom:** Users receive 'Unauthorized' errors.
- **Solution:**
  - Make sure the user is assigned the correct role in the Permit.io Directory.
  - Check your policy mapping and resource/action names.
  - Ensure your JWT or header is set correctly.
  - Review the server logs for details.

### Method Not Found
- **Symptom:** Errors about unknown or unmapped methods.
- **Solution:**
  - Verify the method is included in your `PERMIT_MCP_KNOWN_METHODS` configuration.
  - Update your policies and middleware settings as needed.

## Debug Logging

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check the server logs for detailed authorization events and errors. 