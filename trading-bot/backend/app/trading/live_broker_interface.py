class LiveBrokerInterface:
    def buy(self, symbol: str, quantity: int):
        raise NotImplementedError("Live trading is disabled in MVP. Use official broker APIs only after approval.")

    def sell(self, symbol: str, quantity: int):
        raise NotImplementedError("Live trading is disabled in MVP. Use official broker APIs only after approval.")
