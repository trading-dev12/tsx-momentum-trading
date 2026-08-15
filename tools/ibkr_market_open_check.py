from core.ibkr_data_provider import IBKRDataProvider


def main():
    provider = IBKRDataProvider(client_id=15)

    try:
        result = provider.get_market_open_price(
            "PAAS.TO",
            "2026-08-05",
        )

        print(result)

    finally:
        provider.disconnect()


if __name__ == "__main__":
    main()