# Testing with Google Stitch MCP

This project uses [Google Stitch MCP](https://stitch.withgoogle.com/) to assist in UI testing and generation.

## Setup Instructions

### 1. Configure Cursor

Create or update the `.cursor/mcp.json` file in the root of the project with the following configuration:

```json
{
  "mcpServers": {
    "stitch": {
      "url": "https://stitch.googleapis.com/mcp",
      "headers": {
        "X-Goog-Api-Key": "YOUR_STITCH_KEY"
      }
    }
  }
}
```

Replace `YOUR_STITCH_KEY` with your actual key (starts with `AQ.`).

### 2. Restart Cursor

After saving the file, restart Cursor to enable the Stitch MCP server.

### 3. Usage for Testing

Once configured, you can ask Cursor to:
- "List my Stitch projects"
- "Create a new project in Stitch for this app"
- "Generate a UI test for the ScannerPage"
- "Verify the UI design in Stitch"

## References
- [Setup Guide](https://stitch.withgoogle.com/docs/mcp/setup/)
- [User Guide](https://stitch.withgoogle.com/docs/mcp/guide/)
- [API Reference](https://stitch.withgoogle.com/docs/mcp/reference/)
