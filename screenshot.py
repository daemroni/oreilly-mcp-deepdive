from mcp.server import MCPServer
from mcp.server.mcpserver.utilities.types import Image

import subprocess
import base64

mcp = MCPServer("ScreenshotDemo")

POWERSHELL_SCRIPT = """
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$ms = New-Object System.IO.MemoryStream
$bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Jpeg)
[Convert]::ToBase64String($ms.ToArray())
"""

@mcp.tool(description="Takes a screenshot of the Windows desktop and returns it as an image. Use this tool whenever the user requests a screenshot.")
def capture_screenshot() -> Image:
    """
    Captures a screenshot of the Windows desktop via PowerShell interop.
    Returns:
        Image: The captured screenshot as a JPEG image object.
    """
    result = subprocess.run(
        ["powershell.exe", "-Command", POWERSHELL_SCRIPT],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Screenshot failed: {result.stderr.strip()}")

    image_data = base64.b64decode(result.stdout.strip())
    return Image(data=image_data, format="jpeg")
if __name__ == "__main__":
    mcp.run()