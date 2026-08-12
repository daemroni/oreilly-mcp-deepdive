from mcp.server import MCPServer
import requests

mcp = MCPServer("Crypto")

@mcp.tool(description="Retrieves the price of a specified cryptocurrency.")
def get_crypto_currency_price(currency: str) -> str:
    """
    Retrieves the price of a specified cryptocurrency.
    Args:
        currency (str): The name of the cryptocurrency.
    Returns:
        str: The price of the cryptocurrency.
    """

    url = "https://api.coingecko.com/api/v3/simple/price?ids={currency}&vs_currencies=usd"

    try:
        response = requests.get(url.format(currency=currency), timeout=10)
        response.raise_for_status()
        data = response.json()
        price = data.get(currency.lower(), {}).get("usd")
        if price is not None:
            return f"The current price of {currency} is ${price:.2f} USD."
        else:
            return f"Price information for {currency} is not available."
    except requests.RequestException as e:
        return f"An error occurred while fetching the price: {str(e)}"

if __name__ == "__main__":
    mcp.run()